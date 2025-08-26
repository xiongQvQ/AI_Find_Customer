import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
export declare const inputTagProps: {
    readonly modelValue: {
        readonly type: import("vue").PropType<string[]>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly max: NumberConstructor;
    readonly tagType: {
        readonly default: "info";
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "primary" | "success" | "warning" | "info" | "danger", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        readonly __epPropKey: true;
    };
    readonly tagEffect: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "dark" | "light" | "plain", unknown, "light", boolean>;
    readonly trigger: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "Enter" | "Space") | (() => "Enter" | "Space") | ((new (...args: any[]) => "Enter" | "Space") | (() => "Enter" | "Space"))[], unknown, unknown, string, boolean>;
    readonly draggable: BooleanConstructor;
    readonly delimiter: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, RegExpConstructor], unknown, unknown, "", boolean>;
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly clearable: BooleanConstructor;
    readonly clearIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly validateEvent: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly readonly: BooleanConstructor;
    readonly autofocus: BooleanConstructor;
    readonly id: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, undefined, boolean>;
    readonly tabindex: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, 0, boolean>;
    readonly maxlength: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly minlength: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly placeholder: StringConstructor;
    readonly autocomplete: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "off", boolean>;
    readonly saveOnBlur: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly collapseTags: BooleanConstructor;
    readonly collapseTagsTooltip: BooleanConstructor;
    readonly maxCollapseTags: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 1, boolean>;
    readonly ariaLabel: StringConstructor;
};
export type InputTagProps = ExtractPropTypes<typeof inputTagProps>;
export type InputTagPropsPublic = __ExtractPublicPropTypes<typeof inputTagProps>;
export declare const inputTagEmits: {
    "update:modelValue": (value?: string[]) => boolean;
    change: (value?: string[]) => boolean;
    input: (value: string) => boolean;
    'add-tag': (value: string | string[]) => boolean;
    'remove-tag': (value: string) => boolean;
    focus: (evt: FocusEvent) => boolean;
    blur: (evt: FocusEvent) => boolean;
    clear: () => boolean;
};
export type InputTagEmits = typeof inputTagEmits;
