import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { Dayjs } from 'dayjs';
export declare const basicDateTableProps: {
    readonly showWeekNumber: BooleanConstructor;
    readonly selectionMode: import("element-plus/es/utils").EpPropFinalized<StringConstructor, string, unknown, string, boolean>;
    readonly cellClassName: {
        readonly type: import("vue").PropType<import("./shared").CellClassNameType>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabledDate: {
        readonly type: import("vue").PropType<import("./shared").DisabledDateType>;
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
    readonly rangeState: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => import("./shared").RangeState) | (() => import("./shared").RangeState) | ((new (...args: any[]) => import("./shared").RangeState) | (() => import("./shared").RangeState))[], unknown, unknown, () => {
        endDate: null;
        selecting: boolean;
    }, boolean>;
    readonly disabled: BooleanConstructor;
};
export declare const basicDateTableEmits: string[];
export type BasicDateTableProps = ExtractPropTypes<typeof basicDateTableProps>;
export type BasicDateTablePropsPublic = __ExtractPublicPropTypes<typeof basicDateTableProps>;
export type BasicDateTableEmits = typeof basicDateTableEmits;
export type RangePickerEmits = {
    minDate: Dayjs;
    maxDate: null;
};
export type DatePickerEmits = Dayjs;
export type DatesPickerEmits = Dayjs[];
export type MonthsPickerEmits = Dayjs[];
export type YearsPickerEmits = Dayjs[];
export type WeekPickerEmits = {
    year: number;
    week: number;
    value: string;
    date: Dayjs;
};
export type DateTableEmits = RangePickerEmits | DatePickerEmits | DatesPickerEmits | WeekPickerEmits;
