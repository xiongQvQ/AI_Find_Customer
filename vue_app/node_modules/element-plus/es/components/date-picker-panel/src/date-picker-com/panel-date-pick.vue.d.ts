import dayjs from 'dayjs';
declare function __VLS_template(): {
    sidebar?(_: {
        class: string;
    }): any;
    "prev-year"?(_: {}): any;
    "prev-month"?(_: {}): any;
    "next-month"?(_: {}): any;
    "next-year"?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    readonly parsedValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => dayjs.Dayjs | [dayjs.Dayjs, dayjs.Dayjs]) | (() => import("element-plus/es/components/time-picker").DayOrDays) | ((new (...args: any[]) => dayjs.Dayjs | [dayjs.Dayjs, dayjs.Dayjs]) | (() => import("element-plus/es/components/time-picker").DayOrDays))[], unknown, unknown>>;
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
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    "panel-change": (...args: any[]) => void;
    pick: (...args: any[]) => void;
    "set-picker-option": (...args: any[]) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly parsedValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => dayjs.Dayjs | [dayjs.Dayjs, dayjs.Dayjs]) | (() => import("element-plus/es/components/time-picker").DayOrDays) | ((new (...args: any[]) => dayjs.Dayjs | [dayjs.Dayjs, dayjs.Dayjs]) | (() => import("element-plus/es/components/time-picker").DayOrDays))[], unknown, unknown>>;
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
}>> & {
    onPick?: ((...args: any[]) => any) | undefined;
    "onPanel-change"?: ((...args: any[]) => any) | undefined;
    "onSet-picker-option"?: ((...args: any[]) => any) | undefined;
}, {
    readonly disabled: boolean;
    readonly border: boolean;
    readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly format: string;
    readonly showNow: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showConfirm: boolean;
    readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showWeekNumber: boolean;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
