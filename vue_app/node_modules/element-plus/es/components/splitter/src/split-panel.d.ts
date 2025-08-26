import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type SplitterPanel from './split-panel.vue';
export declare const splitterPanelProps: {
    readonly min: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly max: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly resizable: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly collapsible: BooleanConstructor;
};
export type SplitterPanelProps = ExtractPropTypes<typeof splitterPanelProps>;
export type SplitterPanelPropsPublic = __ExtractPublicPropTypes<typeof splitterPanelProps>;
export type SplitterPanelInstance = InstanceType<typeof SplitterPanel> & unknown;
