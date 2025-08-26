declare function __VLS_template(): {
    prefix?(_: {}): any;
    tag?(_: {
        value: string;
        index: number;
    }): any;
    tag?(_: {
        value: string;
        index: number;
    }): any;
    suffix?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    readonly modelValue: {
        readonly type: import("vue").PropType<string[]>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly max: NumberConstructor;
    readonly tagType: {
        readonly default: "info";
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "primary" | "success" | "warning" | "info" | "danger", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        readonly __epPropKey: true;
    };
    readonly tagEffect: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "dark" | "light" | "plain", unknown, "light", boolean>;
    readonly trigger: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "Enter" | "Space") | (() => "Enter" | "Space") | ((new (...args: any[]) => "Enter" | "Space") | (() => "Enter" | "Space"))[], unknown, unknown, string, boolean>;
    readonly draggable: BooleanConstructor;
    readonly delimiter: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, RegExpConstructor], unknown, unknown, "", boolean>;
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly clearable: BooleanConstructor;
    readonly clearIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly validateEvent: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly readonly: BooleanConstructor;
    readonly autofocus: BooleanConstructor;
    readonly id: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, undefined, boolean>;
    readonly tabindex: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, 0, boolean>;
    readonly maxlength: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly minlength: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly placeholder: StringConstructor;
    readonly autocomplete: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "off", boolean>;
    readonly saveOnBlur: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly collapseTags: BooleanConstructor;
    readonly collapseTagsTooltip: BooleanConstructor;
    readonly maxCollapseTags: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 1, boolean>;
    readonly ariaLabel: StringConstructor;
}, {
    focus: () => void;
    blur: () => void;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    clear: () => void;
    "update:modelValue": (value?: string[] | undefined) => void;
    change: (value?: string[] | undefined) => void;
    input: (value: string) => void;
    blur: (evt: FocusEvent) => void;
    focus: (evt: FocusEvent) => void;
    "add-tag": (value: string | string[]) => void;
    "remove-tag": (value: string) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly modelValue: {
        readonly type: import("vue").PropType<string[]>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly max: NumberConstructor;
    readonly tagType: {
        readonly default: "info";
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "primary" | "success" | "warning" | "info" | "danger", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        readonly __epPropKey: true;
    };
    readonly tagEffect: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "dark" | "light" | "plain", unknown, "light", boolean>;
    readonly trigger: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "Enter" | "Space") | (() => "Enter" | "Space") | ((new (...args: any[]) => "Enter" | "Space") | (() => "Enter" | "Space"))[], unknown, unknown, string, boolean>;
    readonly draggable: BooleanConstructor;
    readonly delimiter: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, RegExpConstructor], unknown, unknown, "", boolean>;
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly clearable: BooleanConstructor;
    readonly clearIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly validateEvent: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly readonly: BooleanConstructor;
    readonly autofocus: BooleanConstructor;
    readonly id: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, undefined, boolean>;
    readonly tabindex: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, 0, boolean>;
    readonly maxlength: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly minlength: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly placeholder: StringConstructor;
    readonly autocomplete: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "off", boolean>;
    readonly saveOnBlur: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly collapseTags: BooleanConstructor;
    readonly collapseTagsTooltip: BooleanConstructor;
    readonly maxCollapseTags: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 1, boolean>;
    readonly ariaLabel: StringConstructor;
}>> & {
    "onUpdate:modelValue"?: ((value?: string[] | undefined) => any) | undefined;
    onChange?: ((value?: string[] | undefined) => any) | undefined;
    onFocus?: ((evt: FocusEvent) => any) | undefined;
    onBlur?: ((evt: FocusEvent) => any) | undefined;
    onInput?: ((value: string) => any) | undefined;
    onClear?: (() => any) | undefined;
    "onAdd-tag"?: ((value: string | string[]) => any) | undefined;
    "onRemove-tag"?: ((value: string) => any) | undefined;
}, {
    readonly disabled: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly id: string;
    readonly tabindex: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>;
    readonly readonly: boolean;
    readonly trigger: import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => "Enter" | "Space") | (() => "Enter" | "Space") | ((new (...args: any[]) => "Enter" | "Space") | (() => "Enter" | "Space"))[], unknown, unknown>;
    readonly autocomplete: string;
    readonly validateEvent: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
    readonly clearable: boolean;
    readonly autofocus: boolean;
    readonly draggable: boolean;
    readonly collapseTags: boolean;
    readonly maxCollapseTags: number;
    readonly collapseTagsTooltip: boolean;
    readonly tagType: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "primary" | "success" | "warning" | "info" | "danger", unknown>;
    readonly tagEffect: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "dark" | "light" | "plain", unknown>;
    readonly delimiter: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, RegExpConstructor], unknown, unknown>;
    readonly saveOnBlur: import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>;
}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
