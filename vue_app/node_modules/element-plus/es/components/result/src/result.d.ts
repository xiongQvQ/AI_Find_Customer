import type { Component, ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type Result from './result.vue';
export declare const IconMap: {
    readonly primary: "icon-primary";
    readonly success: "icon-success";
    readonly warning: "icon-warning";
    readonly error: "icon-error";
    readonly info: "icon-info";
};
export declare const IconComponentMap: Record<typeof IconMap[keyof typeof IconMap], Component>;
export declare const resultProps: {
    readonly title: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly subTitle: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly icon: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "error" | "primary" | "success" | "warning" | "info", unknown, "info", boolean>;
};
export type ResultProps = ExtractPropTypes<typeof resultProps>;
export type ResultPropsPublic = __ExtractPublicPropTypes<typeof resultProps>;
export type ResultInstance = InstanceType<typeof Result> & unknown;
