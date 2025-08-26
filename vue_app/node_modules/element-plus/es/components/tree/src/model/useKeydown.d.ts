import type TreeStore from './tree-store';
import type { Ref } from 'vue';
interface UseKeydownOption {
    el$: Ref<HTMLElement | null>;
}
export declare function useKeydown({ el$ }: UseKeydownOption, store: Ref<TreeStore>): void;
export {};
