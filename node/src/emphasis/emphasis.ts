/*
 * filename: emphasis.ts
 * date: 10/16/2024
 * author: Tristan Hilbert (aka TFlexSoom)
 * desc: Highlights emphasis worthy corpus prompts and annotations
 *   as signaled by the backend.
 * 
 */

import "./emphasis.css"

import TrieSearch from "trie-search";
import { getJsonElement } from "../document";
import { addNewFormatting, Format, FormatType, getText, render } from "../instance";

const FORMAT_TYPE: FormatType = "emphasis";

function emphasize(
    instanceText: string, 
    emphasisList: Array<string>,
    formatCallback: (format: Format) => void
) {
    const emphasisTrie = new TrieSearch<any>(undefined, {
        splitOnRegEx: false,
    });

    emphasisList.map((item) => emphasisTrie.map(item, item));
    const wordList = instanceText.split(" ");
    let lastWasValid = false;
    let currentIndex = 0;
    let last = "";
    for(const word of wordList) {
        const current = last + word;
        const search = emphasisTrie.search(current);

        if(search.length === 0 && lastWasValid) {
            formatCallback({
                start: currentIndex,
                end: last.length,
                formatType: FORMAT_TYPE,
                option: "",
            })
            currentIndex += last.length;
            currentIndex += (word + ' ').length;
            last = "";
            lastWasValid = false;
            continue;
        }

        if(search.length === 0) {
            currentIndex += (word + " ").length;
            last = "";
            continue;
        }

        if(search.length === 1 && search[0] === current) {
            formatCallback({
                start: currentIndex,
                end: current.length,
                formatType: FORMAT_TYPE,
                option: "",
            })
            currentIndex += (current).length
            last = "";
            lastWasValid = false;
            continue;
        }

        if(search.includes(current)) {
            lastWasValid = true;
        }
        
        last = current + " ";
    }
}

interface Suggestion {
    name: string
    label: string
}

function suggest(suggestions: Array<Suggestion>) {
    try{
        for(const s of suggestions) {
            const elem = document.getElementById(s.name);
            if(elem === null) {
                console.warn("no elem with id " + s.name);
                continue;
            }

            if(elem.classList.contains("multiselect") || elem.classList.contains("radio")) {
                const inputElem = document.getElementById(s.name + ":::" + s.label);
                if(elem === null) {
                    console.warn(`no elem with id ${s.name + ":::" + s.label}`);
                    continue;
                }
                
                inputElem?.parentElement?.classList.add("suggestion");
            }
        }
    } catch(err) {
        console.error(`could not suggest elements`);
    }
}

export function provideEmphasisAndSuggestion() {
    const emphasis = getJsonElement<Array<string>>("emphasis");
    if(emphasis !== undefined) {
        emphasize(getText(), emphasis, addNewFormatting);
        render();
    }

    const suggestions = getJsonElement<Array<Suggestion>>("suggestions");
    if(suggestions !== undefined) {
        suggest(suggestions);
    }
}