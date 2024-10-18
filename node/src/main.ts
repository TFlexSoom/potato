import IntervalTree from '@flatten-js/interval-tree'

import {onlyOne, whetherNone} from "./checkbox"
import { triggerTime } from "./countdown";
import { provideEmphasisAndSuggestion } from "./emphasis"
import { openNav, closeNav, closeNav2, showInstructions} from "./navigation"
import onReady from './new-span';
import { keyupListener, click_to_next, click_to_prev, check_close } from './post';
import { barValue } from './range';
import { changeSpanLabel } from './span';
import { jqueryUITooltip } from './tooltip';


function main() {
  (window as any).onlyOne = onlyOne;
  (window as any).whetherNone = whetherNone;
  (window as any).x = (window as any).setInterval(triggerTime, 1000);
  (window as any).openNav = openNav;
  (window as any).closeNav = closeNav;
  (window as any).closeNav2 = closeNav2;
  (window as any).showInstructions = showInstructions;
  (window as any).click_to_next = click_to_next;
  (window as any).click_to_prev = click_to_prev;
  (window as any).check_close = check_close;
  (window as any).barValue = barValue;
  (window as any).changeSpanLabel = changeSpanLabel;
  (window as any).jqueryUITooltip = jqueryUITooltip;

  document.addEventListener('keyup', keyupListener);
  
  onReady(document);
  provideEmphasisAndSuggestion();
}


(function(){
  'use-strict';

  main();
}())
