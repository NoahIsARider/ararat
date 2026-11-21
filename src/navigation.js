// Walking surfaces are exported from the same dimensions as the Blender structure.
export function createNavigation(data,ground){
  const deck=data.deck,stairs=data.stairs;
  function deckWidth(y){
    const samples=deck.halfWidths;
    if(y<deck.yMin||y>deck.yMax)return 0;
    let i=Math.min(samples.length-2,Math.max(0,Math.floor((y-samples[0][0])/(samples[1][0]-samples[0][0]))));
    const [ya,wa]=samples[i],[yb,wb]=samples[i+1];return wa+(wb-wa)*(y-ya)/(yb-ya);
  }
  function surfaceAt(x,z){
    for(const p of data.landings){if(x>=p.xMin&&x<=p.xMax&&z>=-p.yMax&&z<=-p.yMin)return {kind:'landing',height:p.z};}
    if(x>=stairs.xTop&&x<stairs.xBottom&&z>=-stairs.yMax&&z<=-stairs.yMin){
      const t=(stairs.xBottom-x)/(stairs.xBottom-stairs.xTop);
      const step=Math.min(stairs.count,Math.floor(t*stairs.count+1e-7)+1);
      return {kind:'stair',height:stairs.zBottom+step*(stairs.zTop-stairs.zBottom)/stairs.count};
    }
    const toe=data.toe;
    if(x>=toe.xMin&&x<=toe.xMax&&z>=-toe.yMax&&z<=-toe.yMin){
      const t=(x-toe.xMin)/(toe.xMax-toe.xMin);return {kind:'toe',height:toe.zStart*(1-t)+(ground(toe.xMax,z)+.025)*t};
    }
    if(Math.abs(x)<deckWidth(-z)&&-z>=deck.yMin&&-z<=deck.yMax)return {kind:'deck',height:deck.z};
    return {kind:'ground',height:ground(x,z)};
  }
  return {surfaceAt,deckWidth,heightAt:(x,z)=>surfaceAt(x,z).height};
}
