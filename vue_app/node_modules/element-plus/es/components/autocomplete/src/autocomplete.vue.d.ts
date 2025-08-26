import type { AutocompleteData } from './autocomplete';
import type { StyleValue } from 'vue';
import type { TooltipInstance } from 'element-plus/es/components/tooltip';
import type { InputInstance } from 'element-plus/es/components/input';
declare function __VLS_template(): {
    prepend?(_: {}): any;
    append?(_: {}): any;
    prefix?(_: {}): any;
    suffix?(_: {}): any;
    header?(_: {}): any;
    loading?(_: {}): any;
    default?(_: {
        item: Record<string, any>;
    }): any;
    footer?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    readonly valueKey: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "value", boolean>;
    readonly modelValue: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, "", boolean>;
    readonly debounce: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 300, boolean>;
    readonly placement: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus").Placement) | ((new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus").Placement))[], "top" | "bottom" | "top-start" | "top-end" | "bottom-start" | "bottom-end", unknown, "bottom-start", boolean>;
    readonly fetchSuggestions: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => AutocompleteData | ((queryString: string, cb: import("./autocomplete").AutocompleteFetchSuggestionsCallback) => import("element-plus/es/utils").Awaitable<AutocompleteData> | void)) | (() => import("./autocomplete").AutocompleteFetchSuggestions) | ((new (...args: any[]) => AutocompleteData | ((queryString: string, cb: import("./autocomplete").AutocompleteFetchSuggestionsCallback) => import("element-plus/es/utils").Awaitable<AutocompleteData> | void)) | (() => import("./autocomplete").AutocompleteFetchSuggestions))[], unknown, unknown, () => void, boolean>;
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
    readonly inputStyle: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue) | ((new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue))[], unknown, unknown, () => import("element-plus/es/utils").Mutable<{}>, boolean>;
    readonly autofocus: BooleanConstructor;
    readonly rows: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 2, boolean>;
}, {
    /** @description the index of the currently highlighted item */
    highlightedIndex: import("vue").Ref<number>;
    /** @description autocomplete whether activated */
    activated: import("vue").Ref<boolean>;
    /** @description remote search loading status */
    loading: import("vue").Ref<boolean>;
    /** @description el-input component instance */
    inputRef: import("vue").Ref<InputInstance | undefined>;
    /** @description el-tooltip component instance */
    popperRef: import("vue").Ref<TooltipInstance | undefined>;
    /** @description fetch suggestions result */
    suggestions: import("vue").Ref<Record<string, any>[]>;
    /** @description triggers when a suggestion is clicked */
    handleSelect: (item: any) => Promise<void>;
    /** @description handle keyboard enter event */
    handleKeyEnter: () => Promise<void>;
    /** @description focus the input element */
    focus: () => void;
    /** @description blur the input element */
    blur: () => void;
    /** @description close suggestion */
    close: () => void;
    /** @description highlight an item in a suggestion */
    highlight: (index: number) => void;
    /** @description loading suggestion list */
    getData: (queryString: string) => Promise<void>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    select: (item: Record<string, any>) => void;
    clear: () => void;
    "update:modelValue": (value: string) => void;
    change: (value: string) => void;
    input: (value: string) => void;
    blur: (evt: FocusEvent) => void;
    focus: (evt: FocusEvent) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly valueKey: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "value", boolean>;
    readonly modelValue: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, "", boolean>;
    readonly debounce: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 300, boolean>;
    readonly placement: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus").Placement) | ((new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus").Placement))[], "top" | "bottom" | "top-start" | "top-end" | "bottom-start" | "bottom-end", unknown, "bottom-start", boolean>;
    readonly fetchSuggestions: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => AutocompleteData | ((queryString: string, cb: import("./autocomplete").AutocompleteFetchSuggestionsCallback) => import("element-plus/es/utils").Awaitable<AutocompleteData> | void)) | (() => import("./autocomplete").AutocompleteFetchSuggestions) | ((new (...args: any[]) => AutocompleteData | ((queryString: string, cb: import("./autocomplete").AutocompleteFetchSuggestionsCallback) => import("element-plus/es/utils").Awaitable<AutocompleteData> | void)) | (() => import("./autocomplete").AutocompleteFetchSuggestions))[], unknown, unknown, () => void, boolean>;
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
    readonly inputStyle: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue) | ((new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue))[], unknown, unknown, () => import("element-plus/es/utils").Mutable<{}>, boolean>;
    readonly autofocus: BooleanConstructor;
    readonly rows: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 2, boolean>;
}>> & {
    "onUpdate:modelValue"?: ((value: string) => any) | undefined;
    onChange?: ((value: string) => any) | undefined;
    onFocus?: ((evt: FocusEvent) => any) | undefined;
    onBlur?: ((evt: FocusEvent) => any) | undefined;
    onInput?: ((value: string) => any) | undefined;
    onSelect?: ((item: Record<string, any>) => any) | undefined;
    onClear?: (() => any) | undefined;
}, {
    readonly disabled: boolean;
    readonly id: string;
    readonly type: string;
    readonly modelValue: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>;
    readonly placement: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus").Placement) | ((new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus").Placement))[], "top" | "bottom" | "top-start" | "top-end" | "bottom-start" | "bottom-end", unknown>;
    readonly tabindex: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>;
    readonly readonly: boolean;
    readonly autosize: import("element-plus/es/components/input").InputAutoSize;
    readonly autocomplete: string;
    readonly containerRole: string;
    readonly validateEvent: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly inputStyle: StyleValue;
    readonly rows: number;
    readonly inputmode: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal") | (() => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal" | undefined) | ((new (...args: any[]) => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal") | (() => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal" | undefined))[], unknown, unknown>;
    readonly clearable: boolean;
    readonly showPassword: boolean;
    readonly showWordLimit: boolean;
    readonly autofocus: boolean;
    readonly popperClass: string;
    readonly teleported: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly valueKey: string;
    readonly debounce: number;
    readonly fetchSuggestions: import("./autocomplete").AutocompleteFetchSuggestions;
    readonly triggerOnFocus: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly selectWhenUnmatched: boolean;
    readonly hideLoading: boolean;
    readonly highlightFirstItem: boolean;
    readonly fitInputWidth: boolean;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
