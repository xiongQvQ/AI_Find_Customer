import type { ExtractPropTypes, InjectionKey, TransitionProps, __ExtractPublicPropTypes } from 'vue';
import type Dialog from './dialog.vue';
type DoneFn = (cancel?: boolean) => void;
export type DialogBeforeCloseFn = (done: DoneFn) => void;
export type DialogTransition = string | TransitionProps;
export declare const dialogProps: {
    readonly appendToBody: BooleanConstructor;
    readonly appendTo: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | HTMLElement) | (() => import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement) | ((new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement))[], unknown, unknown>) | ((new (...args: any[]) => string | HTMLElement) | (() => import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement) | ((new (...args: any[]) => string | HTMLElement) | (() => string | HTMLElement))[], unknown, unknown>))[], unknown, unknown, "body", boolean>;
    readonly beforeClose: {
        readonly type: import("vue").PropType<DialogBeforeCloseFn>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly destroyOnClose: BooleanConstructor;
    readonly closeOnClickModal: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly closeOnPressEscape: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly lockScroll: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly modal: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly modalPenetrable: BooleanConstructor;
    readonly openDelay: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 0, boolean>;
    readonly closeDelay: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 0, boolean>;
    readonly top: {
        readonly type: import("vue").PropType<string>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly modelValue: BooleanConstructor;
    readonly modalClass: StringConstructor;
    readonly headerClass: StringConstructor;
    readonly bodyClass: StringConstructor;
    readonly footerClass: StringConstructor;
    readonly width: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly zIndex: {
        readonly type: import("vue").PropType<number>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly trapFocus: BooleanConstructor;
    readonly headerAriaLevel: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "2", boolean>;
    readonly transition: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | TransitionProps) | (() => DialogTransition) | ((new (...args: any[]) => string | TransitionProps) | (() => DialogTransition))[], unknown, unknown, undefined, boolean>;
    readonly center: BooleanConstructor;
    readonly alignCenter: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly closeIcon: {
        readonly type: import("vue").PropType<import("element-plus/es/utils").EpPropMergeType<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown>>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
    readonly draggable: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly overflow: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, undefined, boolean>;
    readonly fullscreen: BooleanConstructor;
    readonly showClose: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, true, boolean>;
    readonly title: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly ariaLevel: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "2", boolean>;
};
export type DialogProps = ExtractPropTypes<typeof dialogProps>;
export type DialogPropsPublic = __ExtractPublicPropTypes<typeof dialogProps>;
export declare const dialogEmits: {
    open: () => boolean;
    opened: () => boolean;
    close: () => boolean;
    closed: () => boolean;
    "update:modelValue": (value: boolean) => boolean;
    openAutoFocus: () => boolean;
    closeAutoFocus: () => boolean;
};
export type DialogEmits = typeof dialogEmits;
export type DialogInstance = InstanceType<typeof Dialog> & unknown;
export interface DialogConfigContext {
    alignCenter?: boolean;
    draggable?: boolean;
    overflow?: boolean;
    transition?: DialogTransition;
}
export declare const dialogContextKey: InjectionKey<DialogConfigContext>;
export {};
