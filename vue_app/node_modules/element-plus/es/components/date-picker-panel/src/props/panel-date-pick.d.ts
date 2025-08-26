import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { DayOrDays } from 'element-plus/es/components/time-picker';
export declare const panelDatePickProps: {
    readonly parsedValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => DayOrDays) | ((new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => DayOrDays))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly visible: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly format: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly type: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | ((new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange"))[], "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange", unknown>>;
        readonly required: true;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly dateFormat: StringConstructor;
    readonly timeFormat: StringConstructor;
    readonly showNow: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly showConfirm: BooleanConstructor;
    readonly showFooter: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly showWeekNumber: BooleanConstructor;
    readonly border: BooleanConstructor;
    readonly disabled: BooleanConstructor;
};
export type PanelDatePickProps = ExtractPropTypes<typeof panelDatePickProps>;
export type PanelDatePickPropsPublic = __ExtractPublicPropTypes<typeof panelDatePickProps>;
