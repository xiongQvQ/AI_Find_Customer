declare function __VLS_template(): {
    "start-collapsible"?(_: {}): any;
    "end-collapsible"?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    index: {
        type: NumberConstructor;
        required: true;
    };
    layout: {
        type: StringConstructor;
        values: readonly ["horizontal", "vertical"];
        default: string;
    };
    resizable: {
        type: BooleanConstructor;
        default: boolean;
    };
    lazy: BooleanConstructor;
    startCollapsible: BooleanConstructor;
    endCollapsible: BooleanConstructor;
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    collapse: (...args: any[]) => void;
    moveStart: (...args: any[]) => void;
    moving: (...args: any[]) => void;
    moveEnd: (...args: any[]) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    index: {
        type: NumberConstructor;
        required: true;
    };
    layout: {
        type: StringConstructor;
        values: readonly ["horizontal", "vertical"];
        default: string;
    };
    resizable: {
        type: BooleanConstructor;
        default: boolean;
    };
    lazy: BooleanConstructor;
    startCollapsible: BooleanConstructor;
    endCollapsible: BooleanConstructor;
}>> & {
    onCollapse?: ((...args: any[]) => any) | undefined;
    onMoveStart?: ((...args: any[]) => any) | undefined;
    onMoving?: ((...args: any[]) => any) | undefined;
    onMoveEnd?: ((...args: any[]) => any) | undefined;
}, {
    layout: string;
    lazy: boolean;
    resizable: boolean;
    startCollapsible: boolean;
    endCollapsible: boolean;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
