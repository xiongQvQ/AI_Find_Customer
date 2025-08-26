import type { AppContext, ExtractPropTypes, VNode, __ExtractPublicPropTypes } from 'vue';
import type { Mutable } from 'element-plus/es/utils';
import type MessageConstructor from './message.vue';
export declare const messageTypes: readonly ["primary", "success", "info", "warning", "error"];
export declare const messagePlacement: readonly ["top", "top-left", "top-right", "bottom", "bottom-left", "bottom-right"];
export declare const MESSAGE_DEFAULT_PLACEMENT = "top";
export type MessageType = typeof messageTypes[number];
export type MessagePlacement = typeof messagePlacement[number];
/** @deprecated please use `MessageType` instead */
export type messageType = MessageType;
export interface MessageConfigContext {
    max?: number;
    grouping?: boolean;
    duration?: number;
    offset?: number;
    showClose?: boolean;
    plain?: boolean;
    placement?: string;
}
export declare const messageDefaults: Mutable<{
    readonly customClass: "";
    readonly dangerouslyUseHTMLString: false;
    readonly duration: 3000;
    readonly icon: undefined;
    readonly id: "";
    readonly message: "";
    readonly onClose: undefined;
    readonly showClose: false;
    readonly type: "info";
    readonly plain: false;
    readonly offset: 16;
    readonly placement: undefined;
    readonly zIndex: 0;
    readonly grouping: false;
    readonly repeatNum: 1;
    readonly appendTo: HTMLElement;
}>;
export declare const messageProps: {
    readonly customClass: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly dangerouslyUseHTMLString: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, false, boolean>;
    readonly duration: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 3000, boolean>;
    readonly icon: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component) | ((new (...args: any[]) => (string | import("vue").Component) & {}) | (() => string | import("vue").Component))[], unknown, unknown, undefined, boolean>;
    readonly id: import("element-plus/es/utils").EpPropFinalized<StringConstructor, unknown, unknown, "", boolean>;
    readonly message: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => string | VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }> | (() => VNode)) | (() => string | VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }> | (() => VNode)) | ((new (...args: any[]) => string | VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }> | (() => VNode)) | (() => string | VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }> | (() => VNode)))[], unknown, unknown, "", boolean>;
    readonly onClose: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => () => void) | (() => () => void) | {
        (): () => void;
        new (): any;
        readonly prototype: any;
    } | ((new (...args: any[]) => () => void) | (() => () => void) | {
        (): () => void;
        new (): any;
        readonly prototype: any;
    })[], unknown, unknown, undefined, boolean>;
    readonly showClose: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, false, boolean>;
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "error" | "primary" | "success" | "warning" | "info", unknown, "info", boolean>;
    readonly plain: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, false, boolean>;
    readonly offset: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 16, boolean>;
    readonly placement: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right", unknown, undefined, boolean>;
    readonly zIndex: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 0, boolean>;
    readonly grouping: import("element-plus/es/utils").EpPropFinalized<BooleanConstructor, unknown, unknown, false, boolean>;
    readonly repeatNum: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, 1, boolean>;
};
export type MessageProps = ExtractPropTypes<typeof messageProps>;
export type MessagePropsPublic = __ExtractPublicPropTypes<typeof messageProps>;
export declare const messageEmits: {
    destroy: () => boolean;
};
export type MessageEmits = typeof messageEmits;
export type MessageInstance = InstanceType<typeof MessageConstructor> & unknown;
export type MessageOptions = Partial<Mutable<Omit<MessageProps, 'id'> & {
    appendTo?: HTMLElement | string;
}>>;
export type MessageParams = MessageOptions | MessageOptions['message'];
export type MessageParamsNormalized = Omit<MessageProps, 'id'> & {
    /**
     * @description set the root element for the message, default to `document.body`
     */
    appendTo: HTMLElement;
};
export type MessageOptionsWithType = Omit<MessageOptions, 'type'>;
export type MessageParamsWithType = MessageOptionsWithType | MessageOptions['message'];
export interface MessageHandler {
    /**
     * @description close the Message
     */
    close: () => void;
}
export type MessageFn = {
    (options?: MessageParams, appContext?: null | AppContext): MessageHandler;
    closeAll(type?: MessageType): void;
    closeAllByPlacement(position: MessagePlacement): void;
};
export type MessageTypedFn = (options?: MessageParamsWithType, appContext?: null | AppContext) => MessageHandler;
export type Message = MessageFn & {
    primary: MessageTypedFn;
    success: MessageTypedFn;
    warning: MessageTypedFn;
    info: MessageTypedFn;
    error: MessageTypedFn;
};
