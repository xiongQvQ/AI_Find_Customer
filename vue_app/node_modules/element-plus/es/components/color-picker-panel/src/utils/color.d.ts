interface ColorOptions {
    enableAlpha: boolean;
    format: string;
    value?: string | null;
}
export default class Color {
    private _hue;
    private _saturation;
    private _value;
    private _alpha;
    private _tiny;
    private _isValid;
    enableAlpha: boolean;
    format: string;
    value: string;
    selected?: boolean;
    constructor(options?: Partial<ColorOptions>);
    set(prop: {
        [key: string]: any;
    } | any, value?: number): void;
    get(prop: string): any;
    toRgb(): import("@ctrl/tinycolor").Numberify<import("@ctrl/tinycolor").RGBA>;
    fromString(value: string): void;
    compare(color: this): boolean;
    doOnChange(): void;
}
export {};
