import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { Dayjs } from 'dayjs';
import type { DayOrDays } from 'element-plus/es/components/time-picker';
declare const selectionModes: string[];
export type RangeState = {
    endDate: null | Dayjs;
    selecting: boolean;
};
export type DisabledDateType = (date: Date) => boolean;
export type CellClassNameType = (date: Date) => string;
export declare const datePickerSharedProps: {
    readonly cellClassName: {
        readonly type: import("vue").PropType<CellClassNameType>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabledDate: {
        readonly type: import("vue").PropType<DisabledDateType>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly date: {
        readonly type: import("vue").PropType<Dayjs>;
        readonly required: true;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly minDate: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Dayjs) | (() => Dayjs | null) | ((new (...args: any[]) => Dayjs) | (() => Dayjs | null))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly maxDate: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Dayjs) | (() => Dayjs | null) | ((new (...args: any[]) => Dayjs) | (() => Dayjs | null))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly parsedValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Dayjs | Dayjs[]) | (() => Dayjs | Dayjs[]) | ((new (...args: any[]) => Dayjs | Dayjs[]) | (() => Dayjs | Dayjs[]))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly rangeState: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => RangeState) | (() => RangeState) | ((new (...args: any[]) => RangeState) | (() => RangeState))[], unknown, unknown, () => {
        endDate: null;
        selecting: boolean;
    }, boolean>;
    readonly disabled: BooleanConstructor;
};
export declare const panelSharedProps: {
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
export declare const panelRangeSharedProps: {
    readonly unlinkPanels: BooleanConstructor;
    readonly visible: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly showConfirm: BooleanConstructor;
    readonly showFooter: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly border: BooleanConstructor;
    readonly disabled: BooleanConstructor;
    readonly parsedValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Dayjs | [Dayjs, Dayjs]) | (() => DayOrDays) | ((new (...args: any[]) => Dayjs | [Dayjs, Dayjs]) | (() => DayOrDays))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
};
export declare const selectionModeWithDefault: (mode: (typeof selectionModes)[number]) => {
    type: StringConstructor;
    values: string[];
    default: string;
};
export declare const rangePickerSharedEmits: {
    pick: (range: [Dayjs, Dayjs]) => boolean;
};
export type RangePickerSharedEmits = typeof rangePickerSharedEmits;
export type PanelRangeSharedProps = ExtractPropTypes<typeof panelRangeSharedProps>;
export type PanelRangeSharedPropsPublic = __ExtractPublicPropTypes<typeof panelRangeSharedProps>;
export {};
