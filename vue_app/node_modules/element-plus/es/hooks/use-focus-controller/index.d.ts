import type { ShallowRef } from 'vue';
import type { MaybeRef } from '@vueuse/core';
interface UseFocusControllerOptions {
    disabled?: MaybeRef<boolean>;
    /**
     * return true to cancel focus
     * @param event FocusEvent
     */
    beforeFocus?: (event: FocusEvent) => boolean | undefined;
    afterFocus?: () => void;
    /**
     * return true to cancel blur
     * @param event FocusEvent
     */
    beforeBlur?: (event: FocusEvent) => boolean | undefined;
    afterBlur?: () => void;
}
export declare function useFocusController<T extends {
    focus: () => void;
}>(target: ShallowRef<T | undefined>, { disabled, beforeFocus, afterFocus, beforeBlur, afterBlur, }?: UseFocusControllerOptions): {
    isFocused: import("vue").Ref<boolean>;
    /** Avoid using wrapperRef and handleFocus/handleBlur together */
    wrapperRef: ShallowRef<HTMLElement | undefined>;
    handleFocus: (event: FocusEvent) => void;
    handleBlur: (event: FocusEvent) => void;
};
export {};
