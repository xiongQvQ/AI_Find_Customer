import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type InputNumber from './input-number.vue';
export declare const inputNumberProps: {
    readonly inputmode: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal") | (() => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal" | undefined) | ((new (...args: any[]) => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal") | (() => "search" | "text" | "none" | "url" | "email" | "tel" | "numeric" | "decimal" | undefined))[], unknown, unknown, undefined, boolean>;
    readonly align: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => "center" | "left" | "right") | (() => "center" | "left" | "right") | ((new (...args: any[]) => "center" | "left" | "right") | (() => "center" | "left" | "right"))[], unknown, unknown, "center", boolean>;
    readonly disabledScientific: BooleanConstructor;
    readonly ariaLabel: StringConstructor;
    readonly id: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, undefined, boolean>;
    readonly step: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 1, boolean>;
    readonly stepStrictly: BooleanConstructor;
    readonly max: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    readonly min: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
    readonly modelValue: {
        readonly type: import("vue").PropType<any>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly readonly: BooleanConstructor;
    readonly disabled: BooleanConstructor;
    readonly size: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "small" | "default" | "large", never>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly controls: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly controlsPosition: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "" | "right", unknown, "", boolean>;
    readonly valueOnClear: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor, null], unknown, unknown, null, boolean>;
    readonly name: StringConstructor;
    readonly placeholder: StringConstructor;
    readonly precision: {
        readonly type: import("vue").PropType<number>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly validateEvent: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
};
export type InputNumberProps = ExtractPropTypes<typeof inputNumberProps>;
export type InputNumberPropsPublic = __ExtractPublicPropTypes<typeof inputNumberProps>;
export declare const inputNumberEmits: {
    change: (cur: number | undefined, prev: number | undefined) => boolean;
    blur: (e: FocusEvent) => boolean;
    focus: (e: FocusEvent) => boolean;
    input: (val: number | null | undefined) => boolean;
    "update:modelValue": (val: number | undefined) => boolean;
};
export type InputNumberEmits = typeof inputNumberEmits;
export type InputNumberInstance = InstanceType<typeof InputNumber> & unknown;
