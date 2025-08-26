import { EmitFn } from 'element-plus/es/utils';
import type { CSSProperties, ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type Select from './select.vue';
import type { Options, Placement, PopperEffect } from 'element-plus/es/components/popper';
import type { Props } from 'element-plus/es/components/select-v2/src/useProps';
export declare const selectProps: {
    ariaLabel: StringConstructor;
    emptyValues: ArrayConstructor;
    valueOnClear: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | number | boolean | Function) | (() => string | number | boolean | Function | null) | ((new (...args: any[]) => string | number | boolean | Function) | (() => string | number | boolean | Function | null))[], unknown, unknown, undefined, boolean>;
    name: StringConstructor;
    id: StringConstructor;
    modelValue: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | number | boolean | Record<string, any> | import("element-plus/es/utils").EpPropMergeType<(ObjectConstructor | BooleanConstructor | NumberConstructor | StringConstructor)[], unknown, unknown>[]) | (() => import("element-plus/es/utils").EpPropMergeType<(ObjectConstructor | BooleanConstructor | NumberConstructor | StringConstructor)[], unknown, unknown> | import("element-plus/es/utils").EpPropMergeType<(ObjectConstructor | BooleanConstructor | NumberConstructor | StringConstructor)[], unknown, unknown>[] | null) | ((new (...args: any[]) => string | number | boolean | Record<string, any> | import("element-plus/es/utils").EpPropMergeType<(ObjectConstructor | BooleanConstructor | NumberConstructor | StringConstructor)[], unknown, unknown>[]) | (() => import("element-plus/es/utils").EpPropMergeType<(ObjectConstructor | BooleanConstructor | NumberConstructor | StringConstructor)[], unknown, unknown> | import("element-plus/es/utils").EpPropMergeType<(ObjectConstructor | BooleanConstructor | NumberConstructor | StringConstructor)[], unknown, unknown>[] | null))[], unknown, unknown, undefined, boolean>;
    autocomplete: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    automaticDropdown: BooleanConstructor;
    size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    effect: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string) | (() => PopperEffect) | ((new (...args: any[]) => string) | (() => PopperEffect))[], unknown, unknown, string, boolean>;
    disabled: BooleanConstructor;
    clearable: BooleanConstructor;
    filterable: BooleanConstructor;
    allowCreate: BooleanConstructor;
    loading: BooleanConstructor;
    popperClass: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    popperStyle: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | CSSProperties) | (() => string | CSSProperties) | ((new (...args: any[]) => string | CSSProperties) | (() => string | CSSProperties))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    popperOptions: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => Partial<Options>) | (() => Partial<Options>) | ((new (...args: any[]) => Partial<Options>) | (() => Partial<Options>))[], unknown, unknown, () => Partial<Options>, boolean>;
    remote: BooleanConstructor;
    loadingText: StringConstructor;
    noMatchText: StringConstructor;
    noDataText: StringConstructor;
    remoteMethod: {
        readonly type: import("vue").PropType<(query: string) => void>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    filterMethod: {
        readonly type: import("vue").PropType<(query: string) => void>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    multiple: BooleanConstructor;
    multipleLimit: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    placeholder: {
        readonly type: import("vue").PropType<string>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    defaultFirstOption: BooleanConstructor;
    reserveKeyword: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    valueKey: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    collapseTags: BooleanConstructor;
    collapseTagsTooltip: BooleanConstructor;
    maxCollapseTags: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    teleported: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    persistent: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    clearIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    fitInputWidth: BooleanConstructor;
    suffixIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    tagType: {
        default: string;
        type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "primary" | "success" | "warning" | "info" | "danger", unknown>>;
        required: false;
        validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    tagEffect: {
        default: string;
        type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "dark" | "light" | "plain", unknown>>;
        required: false;
        validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    validateEvent: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    remoteShowSuffix: BooleanConstructor;
    showArrow: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    offset: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    placement: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => Placement) | ((new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => Placement))[], Placement, unknown, string, boolean>;
    fallbackPlacements: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => Placement[]) | (() => Placement[]) | ((new (...args: any[]) => Placement[]) | (() => Placement[]))[], unknown, unknown, string[], boolean>;
    tabindex: import("element-plus/es/utils").EpPropFinalized<(NumberConstructor | StringConstructor)[], unknown, unknown, number, boolean>;
    appendTo: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | HTMLElement) | (() => import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement) | ((new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement))[], unknown, unknown>) | ((new (...args: any[]) => string | HTMLElement) | (() => import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement) | ((new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement))[], unknown, unknown>))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    options: {
        readonly type: import("vue").PropType<Record<string, any>[]>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    props: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => Props) | (() => Props) | ((new (...args: any[]) => Props) | (() => Props))[], unknown, unknown, () => Required<Props>, boolean>;
};
export declare const selectEmits: {
    "update:modelValue": (val: SelectProps["modelValue"]) => boolean;
    change: (val: SelectProps["modelValue"]) => boolean;
    'popup-scroll': ({ scrollTop, scrollLeft, }: {
        scrollTop: number;
        scrollLeft: number;
    }) => boolean;
    'remove-tag': (val: unknown) => boolean;
    'visible-change': (visible: boolean) => boolean;
    focus: (evt: FocusEvent) => boolean;
    blur: (evt: FocusEvent) => boolean;
    clear: () => boolean;
};
export type SelectProps = ExtractPropTypes<typeof selectProps>;
export type SelectPropsPublic = __ExtractPublicPropTypes<typeof selectProps>;
export type SelectEmits = EmitFn<typeof selectEmits>;
export type SelectInstance = InstanceType<typeof Select> & unknown;
export type SelectOptionProps = Props;
