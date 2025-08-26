import dayjs from 'dayjs';
declare function __VLS_template(): {
    sidebar?(_: {
        class: string;
    }): any;
    "prev-year"?(_: {}): any;
    "prev-year"?(_: {}): any;
    "next-year"?(_: {}): any;
    "next-year"?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    readonly unlinkPanels: BooleanConstructor;
    readonly visible: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly showConfirm: BooleanConstructor;
    readonly showFooter: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly border: BooleanConstructor;
    readonly disabled: BooleanConstructor;
    readonly parsedValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => dayjs.Dayjs | [dayjs.Dayjs, dayjs.Dayjs]) | (() => import("element-plus/es/components/time-picker").DayOrDays) | ((new (...args: any[]) => dayjs.Dayjs | [dayjs.Dayjs, dayjs.Dayjs]) | (() => import("element-plus/es/components/time-picker").DayOrDays))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    [x: string]: (...args: any[]) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly unlinkPanels: BooleanConstructor;
    readonly visible: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly showConfirm: BooleanConstructor;
    readonly showFooter: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly border: BooleanConstructor;
    readonly disabled: BooleanConstructor;
    readonly parsedValue: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => dayjs.Dayjs | [dayjs.Dayjs, dayjs.Dayjs]) | (() => import("element-plus/es/components/time-picker").DayOrDays) | ((new (...args: any[]) => dayjs.Dayjs | [dayjs.Dayjs, dayjs.Dayjs]) | (() => import("element-plus/es/components/time-picker").DayOrDays))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
}>>, {
    readonly disabled: boolean;
    readonly border: boolean;
    readonly visible: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly showConfirm: boolean;
    readonly showFooter: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly unlinkPanels: boolean;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
