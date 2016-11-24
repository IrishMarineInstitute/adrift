L.ParticleDot = L.Class.extend({
  
	initialize: function(latlng, image, map, options) {
		L.Util.setOptions(this, options);
		this._latlng = latlng;
		this._canvas = null;
		this._verticalOffset = 1;
		this._horizontalOffset = 1;
		this._image = image;
		this.onAdd(map);
	},


	onAdd: function(map) {
	  var me = this;
		this._map = map;
		var canvas = this._canvas = document.createElement('img');
		canvas.setAttribute('height',4);
		canvas.setAttribute('width',4);
    canvas.setAttribute('src',this._image);
		canvas.style.position = "absolute";
		map._panes.markerPane.appendChild(this._canvas);
		map.on('viewreset', this._reset, this);
		this._reset();
	},


	onRemove: function(map) {
	  map._panes.markerPane.removeChild(this._canvas);
		map.off('viewreset', this._reset, this);
	},


	getLatLng: function() {
		return this._latlng;
	},


	setLatLng: function(latlng) {
		this._latlng = latlng;
		this._reset();
	},


	_reset: function() {
		var pos = this._map.latLngToLayerPoint(this._latlng).round();
		var canvas = this._canvas;
		
		canvas.style.left = pos.x-this._horizontalOffset + 'px';
		canvas.style.top = pos.y-this._verticalOffset + 'px';
	}
});
