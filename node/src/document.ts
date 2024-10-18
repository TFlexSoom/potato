

export function getJsonElement<T>(elementId: string): T | undefined {
    const elem = document.getElementById(elementId);
    if(elem === null) {
        return undefined;
    }

    try{
        return JSON.parse(elem.textContent as string) as T;
    } catch(err) {
        console.warn(`could not parse json element '${elementId}'. Error: ${err}`);
    }

    return undefined;
}

export function getElementById(elementId: string, name?: string) {
    try {
        return document.getElementById(elementId);
    } catch(e) {
        console.warn(`unable to get ${name || "unknown"}: ${e}`);
    }

    return undefined;
}