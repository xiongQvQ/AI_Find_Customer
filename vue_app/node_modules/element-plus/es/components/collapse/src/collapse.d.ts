import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { Arrayable, Awaitable } from 'element-plus/es/utils';
export type CollapseActiveName = string | number;
export type CollapseModelValue = Arrayable<CollapseActiveName>;
export type CollapseIconPositionType = 'left' | 'right';
export declare const emitChangeFn: (value: CollapseModelValue) => value is string | number | CollapseActiveName[];
export declare const collapseProps: {
    readonly accordion: BooleanConstructor;
    readonly modelValue: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | number | CollapseActiveName[]) | (() => CollapseModelValue) | ((new (...args: any[]) => string | number | CollapseActiveName[]) | (() => CollapseModelValue))[], unknown, unknown, () => [], boolean>;
    readonly expandIconPosition: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "left" | "right") | (() => CollapseIconPositionType) | ((new (...args: any[]) => "left" | "right") | (() => CollapseIconPositionType))[], unknown, unknown, "right", boolean>;
    readonly beforeCollapse: {
        readonly type: import("vue").PropType<(name: CollapseActiveName) => Awaitable<boolean>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
};
export type CollapseProps = ExtractPropTypes<typeof collapseProps>;
export type CollapsePropsPublic = __ExtractPublicPropTypes<typeof collapseProps>;
export declare const collapseEmits: {
    "update:modelValue": (value: CollapseModelValue) => value is string | number | CollapseActiveName[];
    change: (value: CollapseModelValue) => value is string | number | CollapseActiveName[];
};
export type CollapseEmits = typeof collapseEmits;
