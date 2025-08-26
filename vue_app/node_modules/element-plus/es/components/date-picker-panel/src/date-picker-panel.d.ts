declare const _default: import("vue").DefineComponent<{
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
    readonly type: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => import("element-plus").DatePickerType) | ((new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => import("element-plus").DatePickerType))[], unknown, unknown, "date", boolean>;
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
    readonly modelValue: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | number | Date | string[] | [import("element-plus/es/components/time-picker").DateModelType, import("element-plus/es/components/time-picker").DateModelType]) | (() => import("element-plus/es/components/time-picker").ModelValueType) | ((new (...args: any[]) => string | number | Date | string[] | [import("element-plus/es/components/time-picker").DateModelType, import("element-plus/es/components/time-picker").DateModelType]) | (() => import("element-plus/es/components/time-picker").ModelValueType))[], unknown, unknown, "", boolean>;
    readonly defaultValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Date | [Date, Date]) | (() => import("element-plus/es/components/time-picker").SingleOrRange<Date>) | ((new (...args: any[]) => Date | [Date, Date]) | (() => import("element-plus/es/components/time-picker").SingleOrRange<Date>))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly defaultTime: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Date | [Date, Date]) | (() => import("element-plus/es/components/time-picker").SingleOrRange<Date>) | ((new (...args: any[]) => Date | [Date, Date]) | (() => import("element-plus/es/components/time-picker").SingleOrRange<Date>))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly isRange: BooleanConstructor;
}, () => JSX.Element, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, ("update:modelValue" | "calendar-change" | "panel-change" | "visible-change" | "pick")[], "update:modelValue" | "calendar-change" | "panel-change" | "visible-change" | "pick", import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
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
    readonly type: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => import("element-plus").DatePickerType) | ((new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => import("element-plus").DatePickerType))[], unknown, unknown, "date", boolean>;
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
    readonly modelValue: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | number | Date | string[] | [import("element-plus/es/components/time-picker").DateModelType, import("element-plus/es/components/time-picker").DateModelType]) | (() => import("element-plus/es/components/time-picker").ModelValueType) | ((new (...args: any[]) => string | number | Date | string[] | [import("element-plus/es/components/time-picker").DateModelType, import("element-plus/es/components/time-picker").DateModelType]) | (() => import("element-plus/es/components/time-picker").ModelValueType))[], unknown, unknown, "", boolean>;
    readonly defaultValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Date | [Date, Date]) | (() => import("element-plus/es/components/time-picker").SingleOrRange<Date>) | ((new (...args: any[]) => Date | [Date, Date]) | (() => import("element-plus/es/components/time-picker").SingleOrRange<Date>))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly defaultTime: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => Date | [Date, Date]) | (() => import("element-plus/es/components/time-picker").SingleOrRange<Date>) | ((new (...args: any[]) => Date | [Date, Date]) | (() => import("element-plus/es/components/time-picker").SingleOrRange<Date>))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly isRange: BooleanConstructor;
}>> & {
    "onUpdate:modelValue"?: ((...args: any[]) => any) | undefined;
    onPick?: ((...args: any[]) => any) | undefined;
    "onCalendar-change"?: ((...args: any[]) => any) | undefined;
    "onPanel-change"?: ((...args: any[]) => any) | undefined;
    "onVisible-change"?: ((...args: any[]) => any) | undefined;
}, {
    readonly disabled: boolean;
    readonly border: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly type: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => import("element-plus").DatePickerType) | ((new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => import("element-plus").DatePickerType))[], unknown, unknown>;
    readonly modelValue: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | number | Date | string[] | [import("element-plus/es/components/time-picker").DateModelType, import("element-plus/es/components/time-picker").DateModelType]) | (() => import("element-plus/es/components/time-picker").ModelValueType) | ((new (...args: any[]) => string | number | Date | string[] | [import("element-plus/es/components/time-picker").DateModelType, import("element-plus/es/components/time-picker").DateModelType]) | (() => import("element-plus/es/components/time-picker").ModelValueType))[], unknown, unknown>;
    readonly clearable: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly shortcuts: unknown[];
    readonly showNow: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showConfirm: boolean;
    readonly showFooter: boolean;
    readonly showWeekNumber: boolean;
    readonly arrowControl: boolean;
    readonly unlinkPanels: boolean;
    readonly isRange: boolean;
}>;
export default _default;
