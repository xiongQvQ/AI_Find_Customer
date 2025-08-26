import type { SetupContext } from 'vue';
import type { ButtonEmits, ButtonProps } from './button';
export declare const useButton: (props: ButtonProps, emit: SetupContext<ButtonEmits>["emit"]) => {
    _disabled: import("vue").ComputedRef<boolean>;
    _size: import("vue").ComputedRef<"" | "small" | "default" | "large">;
    _type: import("vue").ComputedRef<string>;
    _ref: import("vue").Ref<HTMLButtonElement | undefined>;
    _props: import("vue").ComputedRef<{
        ariaDisabled: boolean;
        disabled: boolean;
        autofocus: boolean;
        type: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "button" | "reset" | "submit", unknown>;
    } | {
        ariaDisabled?: undefined;
        disabled?: undefined;
        autofocus?: undefined;
        type?: undefined;
    }>;
    _plain: import("vue").ComputedRef<import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>>;
    _round: import("vue").ComputedRef<import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>>;
    _text: import("vue").ComputedRef<import("element-plus/es/utils").EpPropMergeType<BooleanConstructor, unknown, unknown>>;
    shouldAddSpace: import("vue").ComputedRef<boolean>;
    handleClick: (evt: MouseEvent) => void;
};
