declare function __VLS_template(): {
    default?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    readonly layout: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "horizontal" | "vertical", unknown, "horizontal", boolean>;
    readonly lazy: BooleanConstructor;
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    resizeStart: (index: number, sizes: number[]) => void;
    resize: (index: number, sizes: number[]) => void;
    resizeEnd: (index: number, sizes: number[]) => void;
    collapse: (index: number, type: "end" | "start", sizes: number[]) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly layout: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "horizontal" | "vertical", unknown, "horizontal", boolean>;
    readonly lazy: BooleanConstructor;
}>> & {
    onResize?: ((index: number, sizes: number[]) => any) | undefined;
    onCollapse?: ((index: number, type: "end" | "start", sizes: number[]) => any) | undefined;
    onResizeStart?: ((index: number, sizes: number[]) => any) | undefined;
    onResizeEnd?: ((index: number, sizes: number[]) => any) | undefined;
}, {
    readonly layout: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "horizontal" | "vertical", unknown>;
    readonly lazy: boolean;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
