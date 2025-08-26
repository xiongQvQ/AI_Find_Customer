import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
export declare const panelMonthRangeProps: {
    readonly unlinkPanels: BooleanConstructor;
    readonly visible: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly showConfirm: BooleanConstructor;
    readonly showFooter: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly border: BooleanConstructor;
    readonly disabled: BooleanConstructor;
    readonly parsedValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays) | ((new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
};
export declare const panelMonthRangeEmits: string[];
export type PanelMonthRangeProps = ExtractPropTypes<typeof panelMonthRangeProps>;
export type PanelMonthRangePropsPublic = __ExtractPublicPropTypes<typeof panelMonthRangeProps>;
