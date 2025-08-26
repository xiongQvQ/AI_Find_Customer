import type { DatePickerType } from './types';
export declare const getPanel: (type: DatePickerType) => ({
    new (...args: any[]): {
        $: import("vue").ComponentInternalInstance;
        $data: {};
        $props: Partial<{
            readonly disabled: boolean;
            readonly border: boolean;
            readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly format: string;
            readonly showNow: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showConfirm: boolean;
            readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showWeekNumber: boolean;
        }> & Omit<Readonly<import("vue").ExtractPropTypes<{
            readonly parsedValue: {
                readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays) | ((new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays))[], unknown, unknown>>;
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
        } & import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, "disabled" | "border" | "visible" | "format" | "showNow" | "showConfirm" | "showFooter" | "showWeekNumber">;
        $attrs: {
            [x: string]: unknown;
        };
        $refs: {
            [x: string]: unknown;
        };
        $slots: import("vue").Slots;
        $root: import("vue").ComponentPublicInstance | null;
        $parent: import("vue").ComponentPublicInstance | null;
        $emit: ((event: "panel-change", ...args: any[]) => void) & ((event: "pick", ...args: any[]) => void) & ((event: "set-picker-option", ...args: any[]) => void);
        $el: any;
        $options: import("vue").ComponentOptionsBase<Readonly<import("vue").ExtractPropTypes<{
            readonly parsedValue: {
                readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays) | ((new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays))[], unknown, unknown>>;
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
        }, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
            "panel-change": (...args: any[]) => void;
            pick: (...args: any[]) => void;
            "set-picker-option": (...args: any[]) => void;
        }, string, {
            readonly disabled: boolean;
            readonly border: boolean;
            readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly format: string;
            readonly showNow: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showConfirm: boolean;
            readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showWeekNumber: boolean;
        }> & {
            beforeCreate?: (() => void) | (() => void)[];
            created?: (() => void) | (() => void)[];
            beforeMount?: (() => void) | (() => void)[];
            mounted?: (() => void) | (() => void)[];
            beforeUpdate?: (() => void) | (() => void)[];
            updated?: (() => void) | (() => void)[];
            activated?: (() => void) | (() => void)[];
            deactivated?: (() => void) | (() => void)[];
            beforeDestroy?: (() => void) | (() => void)[];
            beforeUnmount?: (() => void) | (() => void)[];
            destroyed?: (() => void) | (() => void)[];
            unmounted?: (() => void) | (() => void)[];
            renderTracked?: ((e: import("vue").DebuggerEvent) => void) | ((e: import("vue").DebuggerEvent) => void)[];
            renderTriggered?: ((e: import("vue").DebuggerEvent) => void) | ((e: import("vue").DebuggerEvent) => void)[];
            errorCaptured?: ((err: unknown, instance: import("vue").ComponentPublicInstance | null, info: string) => boolean | void) | ((err: unknown, instance: import("vue").ComponentPublicInstance | null, info: string) => boolean | void)[];
        };
        $forceUpdate: () => void;
        $nextTick: typeof import("vue").nextTick;
        $watch(source: string | Function, cb: Function, options?: import("vue").WatchOptions): import("vue").WatchStopHandle;
    } & Readonly<import("vue").ExtractPropTypes<{
        readonly parsedValue: {
            readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays) | ((new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays))[], unknown, unknown>>;
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
    } & import("vue").ShallowUnwrapRef<{}> & {} & import("vue").ComponentCustomProperties;
    __isFragment?: never;
    __isTeleport?: never;
    __isSuspense?: never;
} & import("vue").ComponentOptionsBase<Readonly<import("vue").ExtractPropTypes<{
    readonly parsedValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays) | ((new (...args: any[]) => import("dayjs").Dayjs | [import("dayjs").Dayjs, import("dayjs").Dayjs]) | (() => import("element-plus").DayOrDays))[], unknown, unknown>>;
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
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    "panel-change": (...args: any[]) => void;
    pick: (...args: any[]) => void;
    "set-picker-option": (...args: any[]) => void;
}, string, {
    readonly disabled: boolean;
    readonly border: boolean;
    readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly format: string;
    readonly showNow: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showConfirm: boolean;
    readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showWeekNumber: boolean;
}> & import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps & (new () => {
    $slots: {
        sidebar?(_: {
            class: string;
        }): any;
        "prev-year"?(_: {}): any;
        "prev-month"?(_: {}): any;
        "next-month"?(_: {}): any;
        "next-year"?(_: {}): any;
    };
})) | ({
    new (...args: any[]): {
        $: import("vue").ComponentInternalInstance;
        $data: {};
        $props: Partial<{
            readonly disabled: boolean;
            readonly border: boolean;
            readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showNow: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showConfirm: boolean;
            readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showWeekNumber: boolean;
            readonly unlinkPanels: boolean;
        }> & Omit<Readonly<import("vue").ExtractPropTypes<{
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
            readonly type: {
                readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | ((new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange"))[], "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange", unknown>>;
                readonly required: true;
                readonly validator: ((val: unknown) => boolean) | undefined;
                __epPropKey: true;
            };
            readonly dateFormat: StringConstructor;
            readonly timeFormat: StringConstructor;
            readonly showNow: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
            readonly showWeekNumber: BooleanConstructor;
        }>> & {
            onPick?: ((...args: any[]) => any) | undefined;
            "onCalendar-change"?: ((...args: any[]) => any) | undefined;
            "onPanel-change"?: ((...args: any[]) => any) | undefined;
            "onSet-picker-option"?: ((...args: any[]) => any) | undefined;
        } & import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, "disabled" | "border" | "visible" | "showNow" | "showConfirm" | "showFooter" | "showWeekNumber" | "unlinkPanels">;
        $attrs: {
            [x: string]: unknown;
        };
        $refs: {
            [x: string]: unknown;
        };
        $slots: import("vue").Slots;
        $root: import("vue").ComponentPublicInstance | null;
        $parent: import("vue").ComponentPublicInstance | null;
        $emit: ((event: "calendar-change", ...args: any[]) => void) & ((event: "panel-change", ...args: any[]) => void) & ((event: "pick", ...args: any[]) => void) & ((event: "set-picker-option", ...args: any[]) => void);
        $el: any;
        $options: import("vue").ComponentOptionsBase<Readonly<import("vue").ExtractPropTypes<{
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
            readonly type: {
                readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | ((new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange"))[], "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange", unknown>>;
                readonly required: true;
                readonly validator: ((val: unknown) => boolean) | undefined;
                __epPropKey: true;
            };
            readonly dateFormat: StringConstructor;
            readonly timeFormat: StringConstructor;
            readonly showNow: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
            readonly showWeekNumber: BooleanConstructor;
        }>> & {
            onPick?: ((...args: any[]) => any) | undefined;
            "onCalendar-change"?: ((...args: any[]) => any) | undefined;
            "onPanel-change"?: ((...args: any[]) => any) | undefined;
            "onSet-picker-option"?: ((...args: any[]) => any) | undefined;
        }, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
            "calendar-change": (...args: any[]) => void;
            "panel-change": (...args: any[]) => void;
            pick: (...args: any[]) => void;
            "set-picker-option": (...args: any[]) => void;
        }, string, {
            readonly disabled: boolean;
            readonly border: boolean;
            readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showNow: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showConfirm: boolean;
            readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showWeekNumber: boolean;
            readonly unlinkPanels: boolean;
        }> & {
            beforeCreate?: (() => void) | (() => void)[];
            created?: (() => void) | (() => void)[];
            beforeMount?: (() => void) | (() => void)[];
            mounted?: (() => void) | (() => void)[];
            beforeUpdate?: (() => void) | (() => void)[];
            updated?: (() => void) | (() => void)[];
            activated?: (() => void) | (() => void)[];
            deactivated?: (() => void) | (() => void)[];
            beforeDestroy?: (() => void) | (() => void)[];
            beforeUnmount?: (() => void) | (() => void)[];
            destroyed?: (() => void) | (() => void)[];
            unmounted?: (() => void) | (() => void)[];
            renderTracked?: ((e: import("vue").DebuggerEvent) => void) | ((e: import("vue").DebuggerEvent) => void)[];
            renderTriggered?: ((e: import("vue").DebuggerEvent) => void) | ((e: import("vue").DebuggerEvent) => void)[];
            errorCaptured?: ((err: unknown, instance: import("vue").ComponentPublicInstance | null, info: string) => boolean | void) | ((err: unknown, instance: import("vue").ComponentPublicInstance | null, info: string) => boolean | void)[];
        };
        $forceUpdate: () => void;
        $nextTick: typeof import("vue").nextTick;
        $watch(source: string | Function, cb: Function, options?: import("vue").WatchOptions): import("vue").WatchStopHandle;
    } & Readonly<import("vue").ExtractPropTypes<{
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
        readonly type: {
            readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | ((new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange"))[], "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange", unknown>>;
            readonly required: true;
            readonly validator: ((val: unknown) => boolean) | undefined;
            __epPropKey: true;
        };
        readonly dateFormat: StringConstructor;
        readonly timeFormat: StringConstructor;
        readonly showNow: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
        readonly showWeekNumber: BooleanConstructor;
    }>> & {
        onPick?: ((...args: any[]) => any) | undefined;
        "onCalendar-change"?: ((...args: any[]) => any) | undefined;
        "onPanel-change"?: ((...args: any[]) => any) | undefined;
        "onSet-picker-option"?: ((...args: any[]) => any) | undefined;
    } & import("vue").ShallowUnwrapRef<{}> & {} & import("vue").ComponentCustomProperties;
    __isFragment?: never;
    __isTeleport?: never;
    __isSuspense?: never;
} & import("vue").ComponentOptionsBase<Readonly<import("vue").ExtractPropTypes<{
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
    readonly type: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | ((new (...args: any[]) => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange") | (() => "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange"))[], "year" | "years" | "month" | "months" | "date" | "dates" | "week" | "datetime" | "datetimerange" | "daterange" | "monthrange" | "yearrange", unknown>>;
        readonly required: true;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly dateFormat: StringConstructor;
    readonly timeFormat: StringConstructor;
    readonly showNow: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly showWeekNumber: BooleanConstructor;
}>> & {
    onPick?: ((...args: any[]) => any) | undefined;
    "onCalendar-change"?: ((...args: any[]) => any) | undefined;
    "onPanel-change"?: ((...args: any[]) => any) | undefined;
    "onSet-picker-option"?: ((...args: any[]) => any) | undefined;
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    "calendar-change": (...args: any[]) => void;
    "panel-change": (...args: any[]) => void;
    pick: (...args: any[]) => void;
    "set-picker-option": (...args: any[]) => void;
}, string, {
    readonly disabled: boolean;
    readonly border: boolean;
    readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showNow: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showConfirm: boolean;
    readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showWeekNumber: boolean;
    readonly unlinkPanels: boolean;
}> & import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps & (new () => {
    $slots: {
        sidebar?(_: {
            class: string;
        }): any;
        "prev-year"?(_: {}): any;
        "prev-year"?(_: {}): any;
        "prev-month"?(_: {}): any;
        "prev-month"?(_: {}): any;
        "next-year"?(_: {}): any;
        "next-year"?(_: {}): any;
        "next-month"?(_: {}): any;
        "next-month"?(_: {}): any;
    };
})) | ({
    new (...args: any[]): {
        $: import("vue").ComponentInternalInstance;
        $data: {};
        $props: Partial<{
            readonly disabled: boolean;
            readonly border: boolean;
            readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showConfirm: boolean;
            readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly unlinkPanels: boolean;
        }> & Omit<Readonly<import("vue").ExtractPropTypes<{
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
        }>> & import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, "disabled" | "border" | "visible" | "showConfirm" | "showFooter" | "unlinkPanels">;
        $attrs: {
            [x: string]: unknown;
        };
        $refs: {
            [x: string]: unknown;
        };
        $slots: import("vue").Slots;
        $root: import("vue").ComponentPublicInstance | null;
        $parent: import("vue").ComponentPublicInstance | null;
        $emit: (event: string, ...args: any[]) => void;
        $el: any;
        $options: import("vue").ComponentOptionsBase<Readonly<import("vue").ExtractPropTypes<{
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
        }>>, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
            [x: string]: (...args: any[]) => void;
        }, string, {
            readonly disabled: boolean;
            readonly border: boolean;
            readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly showConfirm: boolean;
            readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
            readonly unlinkPanels: boolean;
        }> & {
            beforeCreate?: (() => void) | (() => void)[];
            created?: (() => void) | (() => void)[];
            beforeMount?: (() => void) | (() => void)[];
            mounted?: (() => void) | (() => void)[];
            beforeUpdate?: (() => void) | (() => void)[];
            updated?: (() => void) | (() => void)[];
            activated?: (() => void) | (() => void)[];
            deactivated?: (() => void) | (() => void)[];
            beforeDestroy?: (() => void) | (() => void)[];
            beforeUnmount?: (() => void) | (() => void)[];
            destroyed?: (() => void) | (() => void)[];
            unmounted?: (() => void) | (() => void)[];
            renderTracked?: ((e: import("vue").DebuggerEvent) => void) | ((e: import("vue").DebuggerEvent) => void)[];
            renderTriggered?: ((e: import("vue").DebuggerEvent) => void) | ((e: import("vue").DebuggerEvent) => void)[];
            errorCaptured?: ((err: unknown, instance: import("vue").ComponentPublicInstance | null, info: string) => boolean | void) | ((err: unknown, instance: import("vue").ComponentPublicInstance | null, info: string) => boolean | void)[];
        };
        $forceUpdate: () => void;
        $nextTick: typeof import("vue").nextTick;
        $watch(source: string | Function, cb: Function, options?: import("vue").WatchOptions): import("vue").WatchStopHandle;
    } & Readonly<import("vue").ExtractPropTypes<{
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
    }>> & import("vue").ShallowUnwrapRef<{}> & {} & import("vue").ComponentCustomProperties;
    __isFragment?: never;
    __isTeleport?: never;
    __isSuspense?: never;
} & import("vue").ComponentOptionsBase<Readonly<import("vue").ExtractPropTypes<{
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
}>>, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    [x: string]: (...args: any[]) => void;
}, string, {
    readonly disabled: boolean;
    readonly border: boolean;
    readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showConfirm: boolean;
    readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly unlinkPanels: boolean;
}> & import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps & (new () => {
    $slots: {
        sidebar?(_: {
            class: string;
        }): any;
        "prev-year"?(_: {}): any;
        "prev-year"?(_: {}): any;
        "next-year"?(_: {}): any;
        "next-year"?(_: {}): any;
    };
}));
