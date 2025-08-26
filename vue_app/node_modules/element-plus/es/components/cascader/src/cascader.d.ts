import type { CascaderNode, CascaderValue } from 'element-plus/es/components/cascader-panel';
import type { Placement, PopperEffect } from 'element-plus/es/components/popper';
export declare const cascaderProps: {
    emptyValues: ArrayConstructor;
    valueOnClear: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | number | boolean | Function) | (() => string | number | boolean | Function | null) | ((new (...args: any[]) => string | number | boolean | Function) | (() => string | number | boolean | Function | null))[], unknown, unknown, undefined, boolean>;
    size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    placeholder: StringConstructor;
    disabled: BooleanConstructor;
    clearable: BooleanConstructor;
    clearIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    filterable: BooleanConstructor;
    filterMethod: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => (node: CascaderNode, keyword: string) => boolean) | (() => (node: CascaderNode, keyword: string) => boolean) | {
        (): (node: CascaderNode, keyword: string) => boolean;
        new (): any;
        readonly prototype: any;
    } | ((new (...args: any[]) => (node: CascaderNode, keyword: string) => boolean) | (() => (node: CascaderNode, keyword: string) => boolean) | {
        (): (node: CascaderNode, keyword: string) => boolean;
        new (): any;
        readonly prototype: any;
    })[], unknown, unknown, (node: CascaderNode, keyword: string) => boolean, boolean>;
    separator: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, string, boolean>;
    showAllLevels: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    collapseTags: BooleanConstructor;
    maxCollapseTags: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    collapseTagsTooltip: BooleanConstructor;
    maxCollapseTagsTooltipHeight: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(NumberConstructor | StringConstructor)[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    debounce: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    beforeFilter: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => (value: string) => boolean | Promise<any>) | (() => (value: string) => boolean | Promise<any>) | {
        (): (value: string) => boolean | Promise<any>;
        new (): any;
        readonly prototype: any;
    } | ((new (...args: any[]) => (value: string) => boolean | Promise<any>) | (() => (value: string) => boolean | Promise<any>) | {
        (): (value: string) => boolean | Promise<any>;
        new (): any;
        readonly prototype: any;
    })[], unknown, unknown, () => true, boolean>;
    placement: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => Placement) | ((new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => Placement))[], Placement, unknown, string, boolean>;
    fallbackPlacements: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => Placement[]) | (() => Placement[]) | ((new (...args: any[]) => Placement[]) | (() => Placement[]))[], unknown, unknown, string[], boolean>;
    popperClass: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | any)[])[])[])[])[])[])[])[])[])[])[]) | (() => string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | any)[])[])[])[])[])[])[])[])[])[])[]) | ((new (...args: any[]) => string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | any)[])[])[])[])[])[])[])[])[])[])[]) | (() => string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | (string | {
            [x: string]: boolean;
        } | any)[])[])[])[])[])[])[])[])[])[])[]))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    popperStyle: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | import("vue").CSSProperties | import("vue").StyleValue[]) | (() => import("vue").StyleValue) | ((new (...args: any[]) => string | import("vue").CSSProperties | import("vue").StyleValue[]) | (() => import("vue").StyleValue))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    teleported: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    effect: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string) | (() => PopperEffect) | ((new (...args: any[]) => string) | (() => PopperEffect))[], unknown, unknown, string, boolean>;
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
    persistent: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    showCheckedStrategy: import("element-plus/es/utils").EpPropFinalized<StringConstructor, string, unknown, string, boolean>;
    checkOnClickNode: BooleanConstructor;
    showPrefix: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    modelValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | number | import("../../cascader-panel/src/node").CascaderNodePathValue | (import("../../cascader-panel/src/node").CascaderNodeValue | import("../../cascader-panel/src/node").CascaderNodePathValue)[]) | (() => import("../../cascader-panel/src/node").CascaderValue | null) | ((new (...args: any[]) => string | number | import("../../cascader-panel/src/node").CascaderNodePathValue | (import("../../cascader-panel/src/node").CascaderNodeValue | import("../../cascader-panel/src/node").CascaderNodePathValue)[]) | (() => import("../../cascader-panel/src/node").CascaderValue | null))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    options: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => import("element-plus/es/components/cascader-panel").CascaderOption[]) | (() => import("element-plus/es/components/cascader-panel").CascaderOption[]) | ((new (...args: any[]) => import("element-plus/es/components/cascader-panel").CascaderOption[]) | (() => import("element-plus/es/components/cascader-panel").CascaderOption[]))[], unknown, unknown, () => import("element-plus/es/components/cascader-panel").CascaderOption[], boolean>;
    props: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => import("element-plus/es/components/cascader-panel").CascaderProps) | (() => import("element-plus/es/components/cascader-panel").CascaderProps) | ((new (...args: any[]) => import("element-plus/es/components/cascader-panel").CascaderProps) | (() => import("element-plus/es/components/cascader-panel").CascaderProps))[], unknown, unknown, () => import("element-plus/es/components/cascader-panel").CascaderProps, boolean>;
};
export declare const cascaderEmits: {
    "update:modelValue": (value: CascaderValue | null | undefined) => boolean;
    change: (value: CascaderValue | null | undefined) => boolean;
    focus: (evt: FocusEvent) => boolean;
    blur: (evt: FocusEvent) => boolean;
    clear: () => boolean;
    visibleChange: (val: boolean) => boolean;
    expandChange: (val: CascaderValue) => boolean;
    removeTag: (val: CascaderNode["valueByOption"]) => boolean;
};
export type CascaderEmits = typeof cascaderEmits;
