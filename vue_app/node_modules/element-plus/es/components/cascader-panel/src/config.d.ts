import type { PropType } from 'vue';
import type { CascaderConfig, CascaderNodePathValue, CascaderOption, CascaderProps, CascaderValue, RenderLabel } from './node';
export declare const CommonProps: {
    readonly modelValue: {
        readonly type: PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | number | CascaderNodePathValue | (import("./node").CascaderNodeValue | CascaderNodePathValue)[]) | (() => CascaderValue | null) | ((new (...args: any[]) => string | number | CascaderNodePathValue | (import("./node").CascaderNodeValue | CascaderNodePathValue)[]) | (() => CascaderValue | null))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly options: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => CascaderOption[]) | (() => CascaderOption[]) | ((new (...args: any[]) => CascaderOption[]) | (() => CascaderOption[]))[], unknown, unknown, () => CascaderOption[], boolean>;
    readonly props: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => CascaderProps) | (() => CascaderProps) | ((new (...args: any[]) => CascaderProps) | (() => CascaderProps))[], unknown, unknown, () => CascaderProps, boolean>;
};
export declare const DefaultProps: CascaderConfig;
export declare const cascaderPanelProps: {
    border: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, boolean, boolean>;
    renderLabel: {
        readonly type: PropType<RenderLabel>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    modelValue: {
        readonly type: PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | number | CascaderNodePathValue | (import("./node").CascaderNodeValue | CascaderNodePathValue)[]) | (() => CascaderValue | null) | ((new (...args: any[]) => string | number | CascaderNodePathValue | (import("./node").CascaderNodeValue | CascaderNodePathValue)[]) | (() => CascaderValue | null))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    options: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => CascaderOption[]) | (() => CascaderOption[]) | ((new (...args: any[]) => CascaderOption[]) | (() => CascaderOption[]))[], unknown, unknown, () => CascaderOption[], boolean>;
    props: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => CascaderProps) | (() => CascaderProps) | ((new (...args: any[]) => CascaderProps) | (() => CascaderProps))[], unknown, unknown, () => CascaderProps, boolean>;
};
export declare const cascaderPanelEmits: {
    "update:modelValue": (value: CascaderValue | undefined | null) => boolean;
    change: (value: CascaderValue | undefined | null) => boolean;
    close: () => boolean;
    'expand-change': (value: CascaderNodePathValue) => CascaderNodePathValue;
};
export declare const useCascaderConfig: (props: {
    props: CascaderProps;
}) => import("vue").ComputedRef<{
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
}>;
