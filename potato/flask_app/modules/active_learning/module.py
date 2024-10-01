"""
module: active_learning
filename: module.py
date: 09/26/2024
author: David Jurgens and Jiaxin Pei (aka Pedro)
desc: Defines Active Learning for models during collection
"""

from collections import Counter, defaultdict
from itertools import zip_longest
import logging
from random import Random

from sklearn.pipeline import Pipeline
import tqdm

from potato.server_utils.class_utils import get_class
from potato.server_utils.config_utils import config
from potato.server_utils.module_utils import Module, module_getter

_logger = logging.getLogger("ActiveLearning")
_random_instance = Random()
_is_actively_learning: bool = False

@module_getter
def _get_module():
    return Module(
        configuration=ActiveLearningConfiguration,
        start=start
    )

@config
class ActiveLearningConfiguration:
    debug: bool = False
    is_actively_learning: bool = False
    active_learning_schema: list[str] = []
    classifier_name: str = ""
    vectorizer_name: str = ""
    resolution_strategy: str = ""
    classifier_kwargs: dict = {}
    vectorizer_kwargs: dict = {}
    random_sample_percent: float = 5.0
    max_inferred_predictions: int = -1
    item_propertis_text_key: str = ""


def start():
    global _is_actively_learning
    
    if ActiveLearningConfiguration.debug:
        _random_instance.seed(0)
    else:
        _random_instance.seed()

    if not ActiveLearningConfiguration.is_actively_learning:
        return
        
    _is_actively_learning = True

    configs = [
        ActiveLearningConfiguration.classifier_name,
        ActiveLearningConfiguration.vectorizer_name,
        ActiveLearningConfiguration.resolution_strategy,
    ]

    if "" in configs:
        raise Exception(f'Missing configuration in active learning\n{configs}')

def actively_learn():
    global _is_actively_learning

    if not _is_actively_learning:
        _logger.warning(
            "the server is trying to do active learning " 
            + "but this hasn't been configured"
        )
        return
    
    schema_used = ActiveLearningConfiguration.active_learning_schema
    cls_kwargs = ActiveLearningConfiguration.classifier_kwargs
    vectorizer_kwargs = ActiveLearningConfiguration.vectorizer_kwargs
    strategy = ActiveLearningConfiguration.resolution_strategy

    # Collect all the current labels
    instance_to_labels = defaultdict(list)

    for uas in user_to_annotation_state.values():
        for iid, annotation in uas.instance_id_to_labeling.items():
            instance_to_labels[iid].append(annotation)

    # Resolve all the mutiple-annotations to a single one using the provided
    # strategy to get training data
    instance_to_label = {}
    schema_seen = set()
    for iid, annotations in instance_to_labels.items():
        resolved = resolve(annotations, strategy)

        # Prune to just the schema we care about
        if len(schema_used) > 0:
            resolved = {k: resolved[k] for k in schema_used}

        for s in resolved:
            schema_seen.add(s)
        instance_to_label[iid] = resolved

    # Construct a dataframe for easy processing
    texts = []
    # We'll train one classifier for each scheme
    scheme_to_labels = defaultdict(list)
    text_key = ActiveLearningConfiguration.item_properties_text_key
    for iid, schema_to_label in instance_to_label.items():
        # get the text
        text = instance_id_to_data[iid][text_key]
        texts.append(text)
        for s in schema_seen:
            # In some cases where the user has not selected anything but somehow
            # this is considered annotated, we include some dummy label
            label = schema_to_label.get(s, "DUMMY:NONE")

            # HACK: this needs to get fixed for multilabel data and possibly
            # number data
            label = list(label.keys())[0]
            scheme_to_labels[s].append(label)

    scheme_to_classifier = {}

    # Train a classifier for each scheme
    for scheme, labels in scheme_to_labels.items():

        # Sanity check we have more than 1 label
        label_counts = Counter(labels)
        if len(label_counts) < 2:
            _logger.warning(
                (
                    "In the current data, data labeled with %s has only a"
                    + "single unique label, which is insufficient for "
                    + "active learning; skipping..."
                )
                % scheme
            )
            continue

        # Instantiate the classifier and the tokenizer
        cls = get_class(ActiveLearningConfiguration.classifier_name)(**cls_kwargs)
        vectorizer = get_class(ActiveLearningConfiguration.vectorizer_name)(**vectorizer_kwargs)

        # Train the classifier
        clf = Pipeline([("vectorizer", vectorizer), ("classifier", cls)])
        _logger.info("training classifier for %s..." % scheme)
        clf.fit(texts, labels)
        _logger.info("done training classifier for %s" % scheme)
        scheme_to_classifier[scheme] = clf

    # Get the remaining unlabeled instances and start predicting
    unlabeled_ids = [iid for iid in instance_id_to_data if iid not in instance_to_label]
    _random_instance.shuffle(unlabeled_ids)

    perc_random = ActiveLearningConfiguration.random_sample_percent / 100

    # Split to keep some of the data random
    random_ids = unlabeled_ids[int(len(unlabeled_ids) * perc_random) :]
    unlabeled_ids = unlabeled_ids[: int(len(unlabeled_ids) * perc_random)]
    remaining_ids = []

    # Cap how much inference we need to do (important for big datasets)
    max_insts = ActiveLearningConfiguration.max_inferred_predictions
    if max_insts > -1:
        remaining_ids = unlabeled_ids[max_insts:]
        unlabeled_ids = unlabeled_ids[:max_insts]

    # For each scheme, use its classifier to label the data
    scheme_to_predictions = {}
    unlabeled_texts = [instance_id_to_data[iid][text_key] for iid in unlabeled_ids]
    for scheme, clf in scheme_to_classifier.items():
        _logger.info("Inferring labels for %s" % scheme)
        preds = clf.predict_proba(unlabeled_texts)
        scheme_to_predictions[scheme] = preds

    # Figure out which of the instances to prioritize, keeping the specified
    # ratio of random-vs-AL-selected instances.
    ids_and_confidence = []
    _logger.info("Scoring items by model confidence")
    for i, iid in enumerate(tqdm(unlabeled_ids)):
        most_confident_pred = 0
        mp_scheme = None
        for scheme, all_preds in scheme_to_predictions.items():

            preds = all_preds[i, :]
            mp = max(preds)
            if mp > most_confident_pred:
                most_confident_pred = mp
                mp_scheme = scheme
        ids_and_confidence.append((iid, most_confident_pred, mp_scheme))

    # Sort by confidence
    ids_and_confidence = sorted(ids_and_confidence, key=lambda x: x[1])

    # Re-order all of the unlabeled instances
    new_id_order = []
    id_to_selection_type = {}
    for (al, rand_id) in zip_longest(ids_and_confidence, random_ids, fillvalue=None):
        if al:
            new_id_order.append(al[0])
            id_to_selection_type[al[0]] = "%s Classifier" % al[2]
        if rand_id:
            new_id_order.append(rand_id)
            id_to_selection_type[rand_id] = "Random"

    # These are the IDs that weren't in the random sample or that we didn't
    # reorder with active learning
    new_id_order.extend(remaining_ids)

    # Update each user's ordering, preserving the order for any item that has
    # any annotation so that it stays in the front of the users' queues even if
    # they haven't gotten to it yet (but others have)
    already_annotated = list(instance_to_labels.keys())
    for annotation_state in user_to_annotation_state.values():
        annotation_state.reorder_remaining_instances(new_id_order, already_annotated)

    _logger.info("Finished reording instances")


def resolve(annotations, strategy):
    if strategy == "random":
        return _random_instance.choice(annotations)
    raise Exception('Unknonwn annotation resolution strategy: "%s"' % (strategy))
