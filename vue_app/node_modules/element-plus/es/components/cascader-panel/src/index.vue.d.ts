import Node from './node';
import type { CascaderNodeValue, CascaderOption, CascaderValue } from './node';
import type { CascaderMenuInstance } from './instance';
declare function __VLS_template(): {
    empty?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    border: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    renderLabel: {
        readonly type: import("vue").PropType<import("./node").RenderLabel>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    modelValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | number | import("./node").CascaderNodePathValue | (CascaderNodeValue | import("./node").CascaderNodePathValue)[]) | (() => CascaderValue | null) | ((new (...args: any[]) => string | number | import("./node").CascaderNodePathValue | (CascaderNodeValue | import("./node").CascaderNodePathValue)[]) | (() => CascaderValue | null))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    options: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => CascaderOption[]) | (() => CascaderOption[]) | ((new (...args: any[]) => CascaderOption[]) | (() => CascaderOption[]))[], unknown, unknown, () => CascaderOption[], boolean>;
    props: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => import("./node").CascaderProps) | (() => import("./node").CascaderProps) | ((new (...args: any[]) => import("./node").CascaderProps) | (() => import("./node").CascaderProps))[], unknown, unknown, () => import("./node").CascaderProps, boolean>;
}, {
    menuList: import("vue").Ref<CascaderMenuInstance[]>;
    menus: import("vue").Ref<{
        readonly uid: number;
        readonly level: number;
        readonly value: CascaderNodeValue;
        readonly label: string;
        readonly pathNodes: any[];
        readonly pathValues: CascaderNodeValue[];
        readonly pathLabels: string[];
        childrenData: {
            [x: string]: unknown;
            label?: string | undefined;
            value?: CascaderNodeValue | undefined;
            children?: any[] | undefined;
            disabled?: boolean | undefined;
            leaf?: boolean | undefined;
        }[] | undefined;
        children: any[];
        text: string;
        loaded: boolean;
        checked: boolean;
        indeterminate: boolean;
        loading: boolean;
        readonly data: {
            [x: string]: unknown;
            label?: string | undefined;
            value?: CascaderNodeValue | undefined;
            children?: any[] | undefined;
            disabled?: boolean | undefined;
            leaf?: boolean | undefined;
        };
        readonly config: {
            expandTrigger: import("./node").ExpandTrigger;
            multiple: boolean;
            checkStrictly: boolean;
            emitPath: boolean;
            lazy: boolean;
            lazyLoad: import("./node").LazyLoad;
            value: string;
            label: string;
            children: string;
            disabled: string | import("./node").isDisabled;
            leaf: string | import("./node").isLeaf;
            hoverThreshold: number;
            checkOnClickNode: boolean;
            checkOnClickLeaf: boolean;
            showPrefix: boolean;
        };
        readonly parent?: any | undefined;
        readonly root: boolean;
        readonly isDisabled: boolean;
        readonly isLeaf: boolean;
        readonly valueByOption: CascaderNodeValue | CascaderNodeValue[];
        appendChild: (childData: CascaderOption) => Node;
        calcText: (allLevels: boolean, separator: string) => string;
        broadcast: (checked: boolean) => void;
        emit: () => void;
        onParentCheck: (checked: boolean) => void;
        onChildCheck: () => void;
        setCheckState: (checked: boolean) => void;
        doCheck: (checked: boolean) => void;
    }[][]>;
    checkedNodes: import("vue").Ref<{
        readonly uid: number;
        readonly level: number;
        readonly value: CascaderNodeValue;
        readonly label: string;
        readonly pathNodes: any[];
        readonly pathValues: CascaderNodeValue[];
        readonly pathLabels: string[];
        childrenData: {
            [x: string]: unknown;
            label?: string | undefined;
            value?: CascaderNodeValue | undefined;
            children?: any[] | undefined;
            disabled?: boolean | undefined;
            leaf?: boolean | undefined;
        }[] | undefined;
        children: any[];
        text: string;
        loaded: boolean;
        checked: boolean;
        indeterminate: boolean;
        loading: boolean;
        readonly data: {
            [x: string]: unknown;
            label?: string | undefined;
            value?: CascaderNodeValue | undefined;
            children?: any[] | undefined;
            disabled?: boolean | undefined;
            leaf?: boolean | undefined;
        };
        readonly config: {
            expandTrigger: import("./node").ExpandTrigger;
            multiple: boolean;
            checkStrictly: boolean;
            emitPath: boolean;
            lazy: boolean;
            lazyLoad: import("./node").LazyLoad;
            value: string;
            label: string;
            children: string;
            disabled: string | import("./node").isDisabled;
            leaf: string | import("./node").isLeaf;
            hoverThreshold: number;
            checkOnClickNode: boolean;
            checkOnClickLeaf: boolean;
            showPrefix: boolean;
        };
        readonly parent?: any | undefined;
        readonly root: boolean;
        readonly isDisabled: boolean;
        readonly isLeaf: boolean;
        readonly valueByOption: CascaderNodeValue | CascaderNodeValue[];
        appendChild: (childData: CascaderOption) => Node;
        calcText: (allLevels: boolean, separator: string) => string;
        broadcast: (checked: boolean) => void;
        emit: () => void;
        onParentCheck: (checked: boolean) => void;
        onChildCheck: () => void;
        setCheckState: (checked: boolean) => void;
        doCheck: (checked: boolean) => void;
    }[]>;
    handleKeyDown: (e: KeyboardEvent) => void;
    handleCheckChange: (node: Node, checked: boolean, emitClose?: boolean) => void;
    getFlattedNodes: (leafOnly: boolean) => Node[];
    /**
     * @description get an array of currently selected node,(leafOnly) whether only return the leaf checked nodes, default is `false`
     */
    getCheckedNodes: (leafOnly: boolean) => Node[];
    /**
     * @description clear checked nodes
     */
    clearCheckedNodes: () => void;
    calculateCheckedValue: () => void;
    scrollToExpandingNode: () => void;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    "update:modelValue": (value: CascaderValue | null | undefined) => void;
    change: (value: CascaderValue | null | undefined) => void;
    close: () => void;
    "expand-change": (value: import("./node").CascaderNodePathValue) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    border: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    renderLabel: {
        readonly type: import("vue").PropType<import("./node").RenderLabel>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    modelValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | number | import("./node").CascaderNodePathValue | (CascaderNodeValue | import("./node").CascaderNodePathValue)[]) | (() => CascaderValue | null) | ((new (...args: any[]) => string | number | import("./node").CascaderNodePathValue | (CascaderNodeValue | import("./node").CascaderNodePathValue)[]) | (() => CascaderValue | null))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    options: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => CascaderOption[]) | (() => CascaderOption[]) | ((new (...args: any[]) => CascaderOption[]) | (() => CascaderOption[]))[], unknown, unknown, () => CascaderOption[], boolean>;
    props: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => import("./node").CascaderProps) | (() => import("./node").CascaderProps) | ((new (...args: any[]) => import("./node").CascaderProps) | (() => import("./node").CascaderProps))[], unknown, unknown, () => import("./node").CascaderProps, boolean>;
}>> & {
    "onUpdate:modelValue"?: ((value: CascaderValue | null | undefined) => any) | undefined;
    onChange?: ((value: CascaderValue | null | undefined) => any) | undefined;
    onClose?: (() => any) | undefined;
    "onExpand-change"?: ((value: import("./node").CascaderNodePathValue) => any) | undefined;
}, {
    border: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    props: import("./node").CascaderProps;
    options: CascaderOption[];
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
