import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type Autocomplete from './autocomplete.vue';
import type { Placement } from 'element-plus/es/components/popper';
import type { Awaitable } from 'element-plus/es/utils';
export type AutocompleteData = Record<string, any>[];
export type AutocompleteFetchSuggestionsCallback = (data: AutocompleteData) => void;
export type AutocompleteFetchSuggestions = ((queryString: string, cb: AutocompleteFetchSuggestionsCallback) => Awaitable<AutocompleteData> | void) | AutocompleteData;
export declare const autocompleteProps: {
    readonly valueKey: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "value", boolean>;
    readonly modelValue: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, "", boolean>;
    readonly debounce: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 300, boolean>;
    readonly placement: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => Placement) | ((new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => Placement))[], "top" | "bottom" | "top-start" | "top-end" | "bottom-start" | "bottom-end", unknown, "bottom-start", boolean>;
    readonly fetchSuggestions: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => AutocompleteData | ((queryString: string, cb: AutocompleteFetchSuggestionsCallback) => Awaitable<AutocompleteData> | void)) | (() => AutocompleteFetchSuggestions) | ((new (...args: any[]) => AutocompleteData | ((queryString: string, cb: AutocompleteFetchSuggestionsCallback) => Awaitable<AutocompleteData> | void)) | (() => AutocompleteFetchSuggestions))[], unknown, unknown, () => void, boolean>;
    readonly popperClass: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly triggerOnFocus: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly selectWhenUnmatched: BooleanConstructor;
    readonly hideLoading: BooleanConstructor;
    readonly teleported: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly appendTo: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | HTMLElement) | (() => import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement) | ((new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement))[], unknown, unknown>) | ((new (...args: any[]) => string | HTMLElement) | (() => import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement) | ((new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement))[], unknown, unknown>))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly highlightFirstItem: BooleanConstructor;
    readonly fitInputWidth: BooleanConstructor;
    readonly inputmode: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal") | (() => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal" | undefined) | ((new (...args: any[]) => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal") | (() => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal" | undefined))[], unknown, unknown, undefined, boolean>;
    readonly name: StringConstructor;
    readonly ariaLabel: StringConstructor;
    readonly id: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, undefined, boolean>;
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: BooleanConstructor;
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
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "text", boolean>;
    readonly resize: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "none" | "both" | "horizontal" | "vertical", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly autosize: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => boolean | {
        minRows?: number;
        maxRows?: number;
    }) | (() => import("element-plus/es/components/input").InputAutoSize) | ((new (...args: any[]) => boolean | {
        minRows?: number;
        maxRows?: number;
    }) | (() => import("element-plus/es/components/input").InputAutoSize))[], unknown, unknown, false, boolean>;
    readonly autocomplete: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "off", boolean>;
    readonly formatter: {
        readonly type: import("vue").PropType<Function>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly parser: {
        readonly type: import("vue").PropType<Function>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly placeholder: {
        readonly type: import("vue").PropType<string>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly form: {
        readonly type: import("vue").PropType<string>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly readonly: BooleanConstructor;
    readonly clearable: BooleanConstructor;
    readonly clearIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly showPassword: BooleanConstructor;
    readonly showWordLimit: BooleanConstructor;
    readonly suffixIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly prefixIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly containerRole: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, undefined, boolean>;
    readonly tabindex: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, 0, boolean>;
    readonly validateEvent: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly inputStyle: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | import("vue").CSSProperties | import("vue").StyleValue[]) | (() => import("vue").StyleValue) | ((new (...args: any[]) => string | import("vue").CSSProperties | import("vue").StyleValue[]) | (() => import("vue").StyleValue))[], unknown, unknown, () => import("element-plus/es/utils").Mutable<{}>, boolean>;
    readonly autofocus: BooleanConstructor;
    readonly rows: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 2, boolean>;
};
export type AutocompleteProps = ExtractPropTypes<typeof autocompleteProps>;
export type AutocompletePropsPublic = __ExtractPublicPropTypes<typeof autocompleteProps>;
export declare const autocompleteEmits: {
    "update:modelValue": (value: string) => boolean;
    input: (value: string) => boolean;
    change: (value: string) => boolean;
    focus: (evt: FocusEvent) => boolean;
    blur: (evt: FocusEvent) => boolean;
    clear: () => boolean;
    select: (item: Record<string, any>) => boolean;
};
export type AutocompleteEmits = typeof autocompleteEmits;
export type AutocompleteInstance = InstanceType<typeof Autocomplete> & unknown;
