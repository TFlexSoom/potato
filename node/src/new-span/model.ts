
import IntervalTree, { Interval } from "@flatten-js/interval-tree";

let tree = new IntervalTree();

interface AnnotationValue {
    low: number
    high: number
    span: string
    labels: string[]
    colors: number[]
}

// function fromJson(json: Iterable<AnnotationRange>) {
//     json.map(())

//     for(var i = 0; i < json.length; i ++) {
//         var value = json[i];
//         var interval = [item["start"], item["end"]];
//         if(!tree.intersect_any(interval)) {
//             tree = insertOne(tree, interval, value);
//             continue;
//         }

//         var others = getCollisions(tree, interval)
//         tree = removeMany(tree, others);
//         group = makeUnique(annotationValue(
//             item["start"],
//             item["end"],
//             item["span"],
//             [item["label"]],
//             [item["color"]]
//         ), others);
//         tree = insertMany(tree, group);
//     }
//     return tree;
// }

function insertOne(tree: IntervalTree, value: AnnotationValue) {
    var interval = new Interval(value.low, value.high);
        
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
        tree.remove(new Interval(value.low, value.high), value);
    }

    return tree;
}

function removeCollisions(tree: IntervalTree, interval: Interval) {
    var others = tree.search(interval);
    return removeMany(tree, others.values());
}

function makeUnique(perpetrator: AnnotationValue, victims: Iterable<AnnotationValue>) {
    // The Perpetrator collides with all victims
    // none of the victims collide with eachother
    // create a unique set of inserts where no one collides

    var unmet = new IntervalTree();
    const perpLow = perpetrator.low;
    const perpHigh = perpetrator.high;
    unmet.insert([perpLow, perpHigh], [perpLow, perpHigh]);
    var result = [] as AnnotationValue[];
    for(const victim of victims) {
        var hits = unmet.search(new Interval(victim.low, victim.high)) // there will only ever be 1 hit
        if (hits.length > 1) {
            throw Error("Tristan's Algorithm is wrong");
        }

        var hitLow = hits[0][0];
        var hitHigh = hits[0][1];
        unmet.remove([hitLow, hitHigh]);

        if(victim.low < hitLow) {
            result.push({
                low: victim.low,
                high: hitLow,
                span: victim.span.substring(0, hitLow - victim.low),
                labels: victim.labels,
                colors: victim.colors,
        });

            result.push(annotationValue(
                hitLow,
                victim.high,
                victim.span.substring(hitLow - victim.low),
                victim.labels.concat(perpetrator.labels),
                victim.colors.concat(perpetrator.colors)
            ));

            unmet.insert([victim.high, hitHigh], [victim.high, hitHigh]);
        } else if (victim.high > hitHigh) {
            result.push(annotationValue(
                hitHigh,
                victim.high,
                victim.span.substring(hitHigh - victim.low),
                victim.labels,
                victim.colors,
            ));

            result.push(annotationValue(
                victim.low,
                hitHigh,
                victim.span.substring(0,  hitHigh - victim.low),
                victim.labels.concat(perpetrator.labels),
                victim.colors.concat(perpetrator.colors)
            ));

            unmet.insert([hitLow, victim.low], [hitLow, victim.low]);
        } else if (victim.low === hitLow && victim.high === hitHigh){
            result.push(annotationValue(
                hitLow,
                hitHigh,
                victim.span,
                victim.labels.concat(perpetrator.labels),
                victim.colors.concat(perpetrator.colors),
            ));
        } else {
            result.push(annotationValue(
                victim.low,
                victim.high,
                victim.span,
                victim.labels.concat(perpetrator.labels),
                victim.colors.concat(perpetrator.colors),
            ));

            if(hitLow !== victim.low) {
                unmet.insert([hitLow, victim.low], [hitLow, victim.low]);
            }

            if(hitHigh !== victim.high) {
                unmet.insert([victim.high, hitHigh], [victim.high, hitHigh]);
            }
        }
    }

    for(var i = 0; i < unmet.keys.length; i ++) {
        var hit = unmet.keys[i];

        result.push(annotationValue(
            hit[0],
            hit[1],
            perpetrator.span.substring(hit[0] - perpLow, hit[1] - perpLow),
            perpetrator.labels,
            perpetrator.colors
        ));
    }

    return result;
}


function removeAnnotations(range) {
    annotations = removeCollisions(annotations, [range.start, range.end]);
}

function updateAnnotations(range) {
    var others = getCollisions(annotations, [range.start, range.end])
    if(others.length == 0) {
        annotations.insert([range.start, range.end], {
            low: range.start,
            high: range.end,
            span: instanceText.substring(range.start, range.end),
            labels: [currentLabel],
            colors: [currentColor]
        });

        return;
    }

    
    annotations = removeMany(annotations, others);
    var group = makeUnique(annotationValue(
        range.start,
        range.end,
        instanceText.substring(range.start, range.end),
        [currentLabel],
        [currentColor]
    ), others);

    console.log(group);

    annotations = insertMany(annotations, group);
}
