import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { ModelValueType, SingleOrRange } from 'element-plus/es/components/time-picker';
import type { DatePickerType } from '../types';
export declare const datePickerPanelProps: {
    readonly disabledDate: {
        readonly type: import("vue").PropType<Function>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly cellClassName: {
        readonly type: import("vue").PropType<Function>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly shortcuts: import("element-plus/es/utils").EpPropFinalized<ArrayConstructor, unknown, unknown, () => never[], boolean>;
    readonly arrowControl: BooleanConstructor;
    readonly unlinkPanels: BooleanConstructor;
    readonly showNow: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly showConfirm: BooleanConstructor;
    readonly showFooter: BooleanConstructor;
    readonly showWeekNumber: BooleanConstructor;
    readonly type: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => DatePickerType) | ((new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => DatePickerType))[], unknown, unknown, "date", boolean>;
    readonly clearable: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly border: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly disabledHours: {
        readonly type: import("vue").PropType<import("element-plus/es/components/time-picker").GetDisabledHours>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabledMinutes: {
        readonly type: import("vue").PropType<import("element-plus/es/components/time-picker").GetDisabledMinutes>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabledSeconds: {
        readonly type: import("vue").PropType<import("element-plus/es/components/time-picker").GetDisabledSeconds>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly valueFormat: StringConstructor;
    readonly dateFormat: StringConstructor;
    readonly timeFormat: StringConstructor;
    readonly disabled: BooleanConstructor;
    readonly modelValue: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | number | Date | string[] | [import("element-plus/es/components/time-picker").DateModelType, import("element-plus/es/components/time-picker").DateModelType]) | (() => ModelValueType) | ((new (...args: any[]) => string | number | Date | string[] | [import("element-plus/es/components/time-picker").DateModelType, import("element-plus/es/components/time-picker").DateModelType]) | (() => ModelValueType))[], unknown, unknown, "", boolean>;
    readonly defaultValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Date | [Date, Date]) | (() => SingleOrRange<Date>) | ((new (...args: any[]) => Date | [Date, Date]) | (() => SingleOrRange<Date>))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly defaultTime: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Date | [Date, Date]) | (() => SingleOrRange<Date>) | ((new (...args: any[]) => Date | [Date, Date]) | (() => SingleOrRange<Date>))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly isRange: BooleanConstructor;
};
export type DatePickerPanelProps = ExtractPropTypes<typeof datePickerPanelProps>;
export type DatePickerPanelPropsPublic = __ExtractPublicPropTypes<typeof datePickerPanelProps>;
