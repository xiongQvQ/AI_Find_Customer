import type { PanelItemState } from '../type';
export declare function getCollapsible(collapsible: boolean | {
    start?: boolean;
    end?: boolean;
}): {
    start?: boolean;
    end?: boolean;
};
export declare function isCollapsible(panel: PanelItemState | null | undefined, size: number, nextPanel: PanelItemState | null | undefined, nextSize: number): boolean;
