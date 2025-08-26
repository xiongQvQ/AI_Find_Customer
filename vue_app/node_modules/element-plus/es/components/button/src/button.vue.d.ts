declare function __VLS_template(): {
    loading?(_: {}): any;
    icon?(_: {}): any;
    default?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: BooleanConstructor;
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "" | "text" | "default" | "primary" | "success" | "warning" | "info" | "danger", unknown, "", boolean>;
    readonly icon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly nativeType: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "button" | "reset" | "submit", unknown, "button", boolean>;
    readonly loading: BooleanConstructor;
    readonly loadingIcon: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown, () => any, boolean>;
    readonly plain: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly text: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly link: BooleanConstructor;
    readonly bg: BooleanConstructor;
    readonly autofocus: BooleanConstructor;
    readonly round: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly circle: BooleanConstructor;
    readonly color: StringConstructor;
    readonly dark: BooleanConstructor;
    readonly autoInsertSpace: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly tag: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown, "button", boolean>;
}, {
    /** @description button html element */
    ref: import("vue").Ref<HTMLButtonElement | undefined>;
    /** @description button size */
    size: import("vue").ComputedRef<"" | "small" | "default" | "large">;
    /** @description button type */
    type: import("vue").ComputedRef<string>;
    /** @description button disabled */
    disabled: import("vue").ComputedRef<boolean>;
    /** @description whether adding space */
    shouldAddSpace: import("vue").ComputedRef<boolean>;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    click: (evt: MouseEvent) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: BooleanConstructor;
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "" | "text" | "default" | "primary" | "success" | "warning" | "info" | "danger", unknown, "", boolean>;
    readonly icon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly nativeType: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "button" | "reset" | "submit", unknown, "button", boolean>;
    readonly loading: BooleanConstructor;
    readonly loadingIcon: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown, () => any, boolean>;
    readonly plain: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly text: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly link: BooleanConstructor;
    readonly bg: BooleanConstructor;
    readonly autofocus: BooleanConstructor;
    readonly round: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly circle: BooleanConstructor;
    readonly color: StringConstructor;
    readonly dark: BooleanConstructor;
    readonly autoInsertSpace: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly tag: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown, "button", boolean>;
}>> & {
    onClick?: ((evt: MouseEvent) => any) | undefined;
}, {
    readonly link: boolean;
    readonly circle: boolean;
    readonly text: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly disabled: boolean;
    readonly round: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly dark: boolean;
    readonly type: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "text" | "default" | "primary" | "success" | "warning" | "info" | "danger", unknown>;
    readonly bg: boolean;
    readonly loading: boolean;
    readonly autofocus: boolean;
    readonly tag: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>;
    readonly plain: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly autoInsertSpace: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly nativeType: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "button" | "reset" | "submit", unknown>;
    readonly loadingIcon: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
