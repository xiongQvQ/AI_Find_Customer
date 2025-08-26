import type { ComputedRef, Ref, StyleValue } from 'vue';
import type { CascaderNode, CascaderPanelInstance, CascaderValue, Tag } from 'element-plus/es/components/cascader-panel';
declare function __VLS_template(): {
    prefix?(_: {}): any;
    tag?(_: {
        data: Tag[];
        deleteTag: (tag: Tag) => void;
    }): any;
    header?(_: {}): any;
    empty?(_: {}): any;
    empty?(_: {}): any;
    "suggestion-item"?(_: {
        item: CascaderNode;
    }): any;
    footer?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
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
    placement: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus/es/components/popper").Placement) | ((new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus/es/components/popper").Placement))[], import("element-plus/es/components/popper").Placement, unknown, string, boolean>;
    fallbackPlacements: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => import("element-plus/es/components/popper").Placement[]) | (() => import("element-plus/es/components/popper").Placement[]) | ((new (...args: any[]) => import("element-plus/es/components/popper").Placement[]) | (() => import("element-plus/es/components/popper").Placement[]))[], unknown, unknown, string[], boolean>;
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
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue) | ((new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    teleported: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    effect: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string) | (() => import("element-plus/es/components/popper").PopperEffect) | ((new (...args: any[]) => string) | (() => import("element-plus/es/components/popper").PopperEffect))[], unknown, unknown, string, boolean>;
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
}, {
    /**
     * @description get an array of currently selected node,(leafOnly) whether only return the leaf checked nodes, default is `false`
     */
    getCheckedNodes: (leafOnly: boolean) => CascaderNode[] | undefined;
    /**
     * @description cascader panel ref
     */
    cascaderPanelRef: Ref<CascaderPanelInstance | null>;
    /**
     * @description toggle the visible of popper
     */
    togglePopperVisible: (visible?: boolean) => void;
    /**
     * @description cascader content ref
     */
    contentRef: ComputedRef<HTMLElement | undefined>;
    /**
     * @description selected content text
     */
    presentText: ComputedRef<string>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    clear: () => void;
    "update:modelValue": (value: CascaderValue | null | undefined) => void;
    change: (value: CascaderValue | null | undefined) => void;
    blur: (evt: FocusEvent) => void;
    focus: (evt: FocusEvent) => void;
    visibleChange: (val: boolean) => void;
    expandChange: (val: CascaderValue) => void;
    removeTag: (val: import("../../cascader-panel/src/node").CascaderNodeValue | import("../../cascader-panel/src/node").CascaderNodePathValue) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
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
    placement: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus/es/components/popper").Placement) | ((new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus/es/components/popper").Placement))[], import("element-plus/es/components/popper").Placement, unknown, string, boolean>;
    fallbackPlacements: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => import("element-plus/es/components/popper").Placement[]) | (() => import("element-plus/es/components/popper").Placement[]) | ((new (...args: any[]) => import("element-plus/es/components/popper").Placement[]) | (() => import("element-plus/es/components/popper").Placement[]))[], unknown, unknown, string[], boolean>;
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
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue) | ((new (...args: any[]) => string | import("vue").CSSProperties | StyleValue[]) | (() => StyleValue))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    teleported: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    effect: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string) | (() => import("element-plus/es/components/popper").PopperEffect) | ((new (...args: any[]) => string) | (() => import("element-plus/es/components/popper").PopperEffect))[], unknown, unknown, string, boolean>;
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
}>> & {
    "onUpdate:modelValue"?: ((value: CascaderValue | null | undefined) => any) | undefined;
    onChange?: ((value: CascaderValue | null | undefined) => any) | undefined;
    onFocus?: ((evt: FocusEvent) => any) | undefined;
    onBlur?: ((evt: FocusEvent) => any) | undefined;
    onClear?: (() => any) | undefined;
    onVisibleChange?: ((val: boolean) => any) | undefined;
    onExpandChange?: ((val: CascaderValue) => any) | undefined;
    onRemoveTag?: ((val: import("../../cascader-panel/src/node").CascaderNodeValue | import("../../cascader-panel/src/node").CascaderNodePathValue) => any) | undefined;
}, {
    disabled: boolean;
    separator: string;
    props: import("element-plus/es/components/cascader-panel").CascaderProps;
    placement: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus/es/components/popper").Placement) | ((new (...args: any[]) => "top" | "bottom" | "left" | "right" | "auto" | "auto-start" | "auto-end" | "top-start" | "top-end" | "bottom-start" | "bottom-end" | "right-start" | "right-end" | "left-start" | "left-end") | (() => import("element-plus/es/components/popper").Placement))[], import("element-plus/es/components/popper").Placement, unknown>;
    options: import("element-plus/es/components/cascader-panel").CascaderOption[];
    effect: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string) | (() => import("element-plus/es/components/popper").PopperEffect) | ((new (...args: any[]) => string) | (() => import("element-plus/es/components/popper").PopperEffect))[], unknown, unknown>;
    valueOnClear: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | number | boolean | Function) | (() => string | number | boolean | Function | null) | ((new (...args: any[]) => string | number | boolean | Function) | (() => string | number | boolean | Function | null))[], unknown, unknown>;
    validateEvent: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    clearable: boolean;
    fallbackPlacements: import("element-plus/es/components/popper").Placement[];
    teleported: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    persistent: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    debounce: number;
    checkOnClickNode: boolean;
    showPrefix: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    filterable: boolean;
    filterMethod: (node: CascaderNode, keyword: string) => boolean;
    showAllLevels: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    collapseTags: boolean;
    maxCollapseTags: number;
    collapseTagsTooltip: boolean;
    beforeFilter: (value: string) => boolean | Promise<any>;
    tagType: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "primary" | "success" | "warning" | "info" | "danger", unknown>;
    tagEffect: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "dark" | "light" | "plain", unknown>;
    showCheckedStrategy: string;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
