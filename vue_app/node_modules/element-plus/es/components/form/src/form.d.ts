import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { FormItemProp } from './form-item';
export declare const formMetaProps: {
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: BooleanConstructor;
};
export declare const formProps: {
    readonly model: ObjectConstructor;
    readonly rules: {
        readonly type: import("vue").PropType<Partial<Record<string, import("element-plus/es/utils").Arrayable<import("./types").FormItemRule>>>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly labelPosition: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "top" | "left" | "right", unknown, "right", boolean>;
    readonly requireAsteriskPosition: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "left" | "right", unknown, "left", boolean>;
    readonly labelWidth: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, "", boolean>;
    readonly labelSuffix: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly inline: BooleanConstructor;
    readonly inlineMessage: BooleanConstructor;
    readonly statusIcon: BooleanConstructor;
    readonly showMessage: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly validateOnRuleChange: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly hideRequiredAsterisk: BooleanConstructor;
    readonly scrollToError: BooleanConstructor;
    readonly scrollIntoViewOptions: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => boolean | ScrollIntoViewOptions) | (() => boolean | ScrollIntoViewOptions) | ((new (...args: any[]) => boolean | ScrollIntoViewOptions) | (() => boolean | ScrollIntoViewOptions))[], unknown, unknown, true, boolean>;
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly disabled: BooleanConstructor;
};
export type FormProps = ExtractPropTypes<typeof formProps>;
export type FormPropsPublic = __ExtractPublicPropTypes<typeof formProps>;
export type FormMetaProps = ExtractPropTypes<typeof formMetaProps>;
export type FormMetaPropsPublic = __ExtractPublicPropTypes<typeof formMetaProps>;
export declare const formEmits: {
    validate: (prop: FormItemProp, isValid: boolean, message: string) => boolean;
};
export type FormEmits = typeof formEmits;
