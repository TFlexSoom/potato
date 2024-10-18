/*
 * author: Tristan Hilbert
 * date: 10/4/2024
 * filename: controller.js
 * desc: Client Side Model Functionality for new spans. By using Interval Trees we efficiently 
 *   store the ranges for the spans (inserted into the trie as inclusive "intervals")
 */

import IntervalTree, { Interval } from "@flatten-js/interval-tree";
import { AnnotationValue, ColorLabel } from "./types";
import { makeUnique } from "./unqiue";

let instanceText = "";
let current: ColorLabel | undefined = undefined;
let tree = new IntervalTree<AnnotationValue>();

export function setInstanceText(newInstanceText: string) {
    instanceText = newInstanceText;
}

export function getInstanceText() {
    return String(instanceText);
}

export function setCurrent(newColorLabel: ColorLabel | undefined) {
    current = newColorLabel;
}

export function getRanges(): Iterable<AnnotationValue> {
    return tree.values;
}

export function appendSelections(selections: Interval[]) {
    if(current === undefined) {
        for(const selection of selections) {
            removeCollisions(tree, selection);
        }
        return;
    }

    const castedCurrent = current as ColorLabel;
    const annotations = selections.map((selection: Interval) => {
        return {
            start: selection.low as number,
            end: selection.high as number,
            span: instanceText.substring(selection.low, selection.high + 1),
            colors: [castedCurrent.color],
            labels: [castedCurrent.label],
        } as AnnotationValue;
    });

    appendServerAnnotations(annotations);
}

export function appendServerAnnotations(annotations: Iterable<AnnotationValue>) {
    for(const annotation of annotations) {
        const interval = new Interval(annotation.start, annotation.end);
        if(!tree.intersect_any(interval)) {
            tree = insertOne(tree, annotation);
            continue;
        }

        const others = tree.search(interval).values()
        tree = removeMany(tree, others);
        const group = makeUnique(annotation, others);
        tree = insertMany(tree, group);
    }
    return tree;
}

function insertOne(tree: IntervalTree, value: AnnotationValue) {
    var interval = new Interval(value.start, value.end);
        
    if(tree.intersect_any(interval)) {
        console.log(`Intersection ${interval} within ${tree.values}`);
        throw Error("Collision Detection in Spans!");
    }

    tree.insert(interval, value);
    return tree;
}

function insertMany(tree: IntervalTree, values: Iterable<AnnotationValue>) {
    for(const value of values) {
        tree = insertOne(tree, value);
    }
    return tree;
}

function removeMany(tree: IntervalTree, values: Iterable<AnnotationValue>) {
    for(const value of values) {
        tree.remove(new Interval(value.start, value.end), value);
    }

    return tree;
}

function removeCollisions(tree: IntervalTree, interval: Interval) {
    var others = tree.search(interval);
    return removeMany(tree, others.values());
}

