import type { ExtractPropTypes, InjectionKey, StyleValue, __ExtractPublicPropTypes } from 'vue';
export declare const cardProps: {
    readonly header: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly footer: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly bodyStyle: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue) | ((new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue))[], unknown, unknown, "", boolean>;
    readonly headerClass: StringConstructor;
    readonly bodyClass: StringConstructor;
    readonly footerClass: StringConstructor;
    readonly shadow: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "always" | "never" | "hover", unknown, undefined, boolean>;
};
export type CardProps = ExtractPropTypes<typeof cardProps>;
export type CardPropsPublic = __ExtractPublicPropTypes<typeof cardProps>;
export interface CardConfigContext {
    shadow?: string;
}
export declare const cardContextKey: InjectionKey<CardConfigContext>;
