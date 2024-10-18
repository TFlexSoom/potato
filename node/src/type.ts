

export function typeAssertion(val: any, type: string) {
    if(typeof(val) !== type) {
        throw Error("Type Error! Expected " + type + " but got " + typeof(val));
    }
}