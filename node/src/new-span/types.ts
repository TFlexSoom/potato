/*
 * author: Tristan Hilbert
 * date: 10/18/2024
 * filename: types.js
 * desc: Types for new span implementation
 */

export interface AnnotationValue {
    start: number
    end: number
    span: string
    labels: string[]
    colors: number[]
}

export interface ColorLabel {
    color: number
    label: string
}