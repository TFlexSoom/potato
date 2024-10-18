/*
 * author: Tristan Hilbert
 * date: 10/18/2024
 * filename: controller.js
 * desc: Make Unique algorithm for taking entries from an Interval Tree we can make
 *   the keys unqiue such that a document can be rendered from colliding intervals.
 */

import IntervalTree, { Interval } from "@flatten-js/interval-tree";
import { AnnotationValue } from "./types";

export function makeUnique(perp: AnnotationValue, victims: Iterable<AnnotationValue>) {
    // The Perpetrator collides with all victims
    // none of the victims collide with eachother
    // create a unique set of intervals where no one collides
    // (perpetrator)          a-----------------a          +
    // (victim)        b--------b                          +
    // (victim)                     c---c                  + 
    // (victim)                                d-------d   +
    //                       =======================
    // (result)        b-----b(bb)aa(ccc)a---a(d)d---d
    // where the (x) sections are `x U a`

    let unmet = new IntervalTree<boolean>();
    unmet.insert([perp.start, perp.end], true);
    let result = [] as AnnotationValue[];
    for(const victim of victims) {
        const hits = unmet.search(new Interval(victim.start, victim.end)) // there will only ever be 1 hit
        if (hits.length > 1) {
            throw Error("Tristan's Algorithm is wrong");
        }

        const [perpStart, perpEnd] = hits[0];
        const perpPiece = new Interval(perpStart, perpEnd)
        unmet.remove(perpPiece);


        const collision = calcCollision(perpPiece, victim);
        result = pushDifferences(result, victim, collision);
        result = pushUnion(result, perp, victim, collision);
        unmet = insertUnmets(unmet, perp, collision);
    }

    return result;
}



function calcCollision(perpPiece: Interval, victim: AnnotationValue) {
    // easier to write than a bunch of if statements
    const toSort = [perpPiece.low, perpPiece.high, victim.start, victim.end];
    toSort.sort((a, b) => a - b);
    return new Interval(toSort[1], toSort[2]);
}

function pushDifferences(
    result: AnnotationValue[],
    victim: AnnotationValue, 
    collision: Interval
) {
    if(victim.start < collision.low) {
        result.push({
            start: victim.start,
            end: collision.low - 1, // inclusive ranges
            span: victim.span.substring(0, collision.low - victim.start),
            colors: victim.colors,
            labels: victim.labels,
        } as AnnotationValue)
    }

    if(victim.end > collision.high) {
        result.push({
            start: collision.high + 1, // inclusive ranges
            end: victim.end,
            span: victim.span.substring(collision.high - victim.start + 1),
            colors: victim.colors,
            labels: victim.labels,
        } as AnnotationValue)
    }

    return result;
}

function pushUnion(
    result: AnnotationValue[],
    perp: AnnotationValue,
    victim: AnnotationValue, 
    collision: Interval
) {
    result.push({
        start: collision.low,
        end: collision.high,
        span: perp.span.substring(collision.low - perp.start, collision.high - collision.low),
        colors: perp.colors.concat(victim.colors),
        labels: perp.labels.concat(victim.labels),
    } as AnnotationValue)

    return result;
}

function insertUnmets(
    unmet: IntervalTree<boolean>,
    perp: AnnotationValue,
    collision: Interval
) {
    if(perp.start < collision.low) {
        unmet.insert(new Interval(perp.start, collision.low - 1))
    }

    if(perp.end > collision.high) {
        unmet.insert(new Interval(collision.high + 1, perp.end));
    }
    
    return unmet;
}