declare function __VLS_template(): {
    icon?(_: {}): any;
    title?(_: {}): any;
    default?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    readonly showAfter: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 0, boolean>;
    readonly hideAfter: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 200, boolean>;
    readonly autoClose: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 0, boolean>;
    readonly title: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly description: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "error" | "primary" | "success" | "warning" | "info", unknown, "info", boolean>;
    readonly closable: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly closeText: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly showIcon: BooleanConstructor;
    readonly center: BooleanConstructor;
    readonly effect: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "dark" | "light", unknown, "light", boolean>;
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    open: () => void;
    close: (evt?: Event | undefined) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly showAfter: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 0, boolean>;
    readonly hideAfter: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 200, boolean>;
    readonly autoClose: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 0, boolean>;
    readonly title: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly description: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "error" | "primary" | "success" | "warning" | "info", unknown, "info", boolean>;
    readonly closable: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly closeText: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly showIcon: BooleanConstructor;
    readonly center: BooleanConstructor;
    readonly effect: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "dark" | "light", unknown, "light", boolean>;
}>> & {
    onOpen?: (() => any) | undefined;
    onClose?: ((evt?: Event | undefined) => any) | undefined;
}, {
    readonly title: string;
    readonly center: boolean;
    readonly type: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "error" | "primary" | "success" | "warning" | "info", unknown>;
    readonly description: string;
    readonly effect: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "dark" | "light", unknown>;
    readonly showAfter: number;
    readonly hideAfter: number;
    readonly autoClose: number;
    readonly closable: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly closeText: string;
    readonly showIcon: boolean;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
