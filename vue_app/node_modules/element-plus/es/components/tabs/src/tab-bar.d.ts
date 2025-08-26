import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { TabPaneName } from './constants';
import type TabBar from './tab-bar.vue';
export declare const tabBarProps: {
    readonly tabs: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]) | (() => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]) | ((new (...args: any[]) => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]) | (() => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]))[], unknown, unknown, () => [], boolean>;
    readonly tabRefs: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }) | (() => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }) | ((new (...args: any[]) => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }) | (() => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }))[], unknown, unknown, () => import("element-plus/es/utils").Mutable<{}>, boolean>;
};
export type TabBarProps = ExtractPropTypes<typeof tabBarProps>;
export type TabBarPropsPublic = __ExtractPublicPropTypes<typeof tabBarProps>;
export type TabBarInstance = InstanceType<typeof TabBar> & unknown;
