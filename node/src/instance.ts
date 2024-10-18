/*
 * filename: instance.ts
 * author: Tristan Hilbert (aka TFlexSoom)
 * date: 10/18/2024
 * desc: Instance that keeps track of formatting alongside document
 *   state for annotation, emphasis, and other formatting fromt he 
 *   server
 */

import IntervalTree, { Interval } from "@flatten-js/interval-tree";
import { getJsonElement } from "./document";

const LINE_FEED_CODE = '\n'.charCodeAt(0);

let hasChanged = false;
let instanceTextElem: HTMLElement;
let instanceText = ""; // Just the text without formatting elements
let instanceHtml = ""; // The html the instance started with
let renderedHtml = ""; // The recently rendered version of the element

let renderingTree: IntervalTree<Format>;

export type FormatType = 
    "linebreak"  | 
    "emphasis"   |
    "annotation" |
    "italics";

export interface Format {
    start: number
    end: number
    formatType: FormatType
    option: string
}

export function readyInstance() {
    const renderedElem = document.getElementById("instance-text");
    if(renderedElem === null) {
        console.warn("no rendering text found");
        return;
    }

    instanceTextElem = renderedElem as HTMLElement;

    const instanceTextJson = (getJsonElement("instance") as {text: string} | undefined)?.text;
    if(instanceTextJson === undefined) {
        console.warn("no instance text found");
        return;
    }

    instanceText = instanceTextElem.innerText;
    instanceHtml = instanceTextJson;
    renderedHtml = instanceTextElem.innerHTML;

    renderingTree = populateRenderingTree(instanceHtml, instanceText, renderedElem.children);
}

export function getText() {
    return instanceText;
}

export function getOriginalHtml() {
    return instanceHtml;
}

export function getHtml() {
    return renderedHtml;
}

export function addNewFormatting(format: Format) {
    // check for any possible siblings.
    // try to extend sibling first
    // otherwise just add
    const search: ArrayIterator<Format> = renderingTree.search(new Interval(format.start, format.end)).values();

    for(const sibling of search) {
        if(sibling.formatType !== format.formatType) {
            continue;
        }

        renderingTree.remove(new Interval(sibling.start, sibling.end));
        format.start = Math.min(sibling.start, format.start);
        format.end = Math.max(sibling.end, format.end);
    }

    
    renderingTree.insert(new Interval(format.start, format.end), format);
    hasChanged = true;
}

const formatToOpenTag: Record<FormatType, (option: string) => string> = {
    "annotation": (option) => 
        `<mark aria-hidden="true" class=" ${option} " >`,
    "emphasis": (_option) => `<mark aria-hidden="true" class=" emphasis ">`,
    "italics": (_option) => `<emph class=" italic ">`,
    "linebreak": (_option) => `<br />`,
}

const formatToClosedTag: Record<FormatType, string> = {
    "annotation": "</mark>",
    "emphasis": "</mark>",
    "italics": "</emph>",
    "linebreak": "",
}

export function render() {
    if(!hasChanged) {
        return;
    }
    hasChanged = false;

    console.log(renderingTree.values);
    let render = "";
    const formats = renderingTree.values;
    const endQueue = [];
    for(let i = 0; i < instanceText.length; i ++) {
        while(formats.length > 0 && i === formats[0].start) {
            const format = formats.shift() as Format;
            render += formatToOpenTag[format?.formatType](format.option);
            endQueue.push(format);
        }

        if(instanceText.charCodeAt(i) !== LINE_FEED_CODE) {
            render += instanceText[i];
        }

        while(endQueue.length > 0 && i === endQueue[0].start) {
            const format = endQueue.shift() as Format;
            render += formatToClosedTag[format?.formatType];
        }
    }

    instanceTextElem.innerHTML = render;
    console.log(instanceHtml);
    console.log(render);
}

// Creating a diff and reconciling would be better than stripping and
// re-rendering
export function clearRangesOfType(formatType: FormatType) {
    for(const format of renderingTree.values) {
        if(format.formatType !== formatType) {
            continue;
        }

        renderingTree.remove(new Interval(format.start, format.end));
    }
}

const tagFormatDictionary: Record<string, Record<string, FormatType | undefined>> = {
    "br": {
        DEFAULT: "linebreak" as FormatType,
    },
    "emph": {
        DEFAULT: "italics" as FormatType,
    },
    "mark": {
        "emphasis": "emphasis" as FormatType,
        "annotation": "annotation" as FormatType,
        DEFAULT: undefined,
    },
}

function populateRenderingTree(html: string, text: string, children: HTMLCollection) {
    hasChanged = true;
    const tree = new IntervalTree<Format>();
    let childrenIndex = 0;
    let textIndex = 0;
    for(let htmlIndex = 0; htmlIndex < html.length; htmlIndex ++) {
        const textChar = text[textIndex];
        const htmlChar = html[htmlIndex];
        if(textChar === htmlChar) {
            textIndex += 1;
            continue;
        }

        if(htmlChar !== "<") {
            continue;
        }

        const child = children[childrenIndex ++] as HTMLElement;
        const tagName = child.tagName.toLowerCase();
        const formatData = child.dataset?.format || "";
        const formatSubDictionary = tagFormatDictionary[tagName];
        const formatting: FormatType | undefined = (
            formatSubDictionary[formatData] || formatSubDictionary?.DEFAULT
        )

        if(formatting === undefined) {
            console.warn(`don't know how to format ${child}`);
            continue;
        }

        const low = textIndex;
        const high = textIndex + child.innerText.length;
        tree.insert(new Interval(low, high), {
            start: low,
            end: high,
            formatType: formatting,
            option: ""
        } as Format);

        while(html[htmlIndex] !== ">" && htmlIndex < html.length) {
            htmlIndex += 1;
        }

        // Edge Case: BRs change to \n in text form
        while(text.charCodeAt(textIndex) === LINE_FEED_CODE) {
            textIndex += 1;
        }
    }

    return tree;
}