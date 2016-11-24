// Attibution: SODA API requests based on this example: https://github.com/chriswhong/soda-leaflet

L.TimeDimension.Layer.SODAHeatMap = L.TimeDimension.Layer.extend({
    _cachedData: {},
    _seriesData: {},

    initialize: function(options) {
        options = options || {};
        options.heatmapOptions = options.heatmapOptions || {};
        var heatmapCfg = {
            radius: 5,
            maxOpacity: .8,
            scaleRadius: false,
            useLocalExtrema: false,
            latField: 'lat',
            lngField: 'lng',
            valueField: 'count'
        };
        if(options.series){
          for(var i=0;i<series.length;i++){
            this._cachedData[series[i].timestamp] = this._toLocations([series[i].points]);
          }
        }
        heatmapCfg = $.extend({}, heatmapCfg, options.heatmapOptions );
        var layer = new HeatmapOverlay(heatmapCfg);
        L.TimeDimension.Layer.prototype.initialize.call(this, layer, options);
        this._currentLoadedTime = 0;
        this._currentTimeData = {
            max: this.options.heatmapMax || 10,
            data: []
        };
    },

    onAdd: function(map) {
        this.map = map;
        L.TimeDimension.Layer.prototype.onAdd.call(this, map);
        map.addLayer(this._baseLayer);
        if (this._timeDimension) {
            this._getDataForTime(this._timeDimension.getCurrentTime());
        }
    },

    _onNewTimeLoading: function(ev) {
        this._getDataForTime(ev.time);
        return;
    },

    isReady: function(time) {
        return (this._currentLoadedTime == time);
    },

    _update: function() {
        this._baseLayer.setData(this._currentTimeData);
        var date = new Date(this._currentLoadedTime);
        $("#utctime").text(date.toISOString());
        $("#localtime").text(date.toString());
        var bounds = this.map.getBounds();
        bounds.extend(L.latLngBounds(this._currentTimeData.data));
        this.map.fitBounds(bounds);
        return true;
    },
    _toLocations: function(data){
            var locations = [];
            for (var i = 0; i < data.length; i++) {
                 locations.push({
                        lat: data[i][0],
                        lng: data[i][1],
                        count: 1
                    });
            }
           return locations;
    },

    _getDataForTime: function(time) {
        var timestamp = new Date(time).toISOString().substring(0,19)+"Z";
        if(this._cachedData[timestamp]){
           this._assignDataForTime(time,this._cachedData[timestamp]);
        }else{
          var url = "point_"+timestamp+".json";
          $.getJSON(url, (function(data) {
            delete this._currentTimeData.data;
            var locations = this._toLocations(data);
            this._cachedData[timestamp] = locations;
            this._assignDataForTime(time,locations);
          }).bind(this));
        }
    },
    _assignDataForTime: function(time,locations){
        this._currentTimeData.data = locations;
        this._currentLoadedTime = time;
        if (this._timeDimension && time == this._timeDimension.getCurrentTime() && !this._timeDimension.isLoading()) {
            this._update();
        }
        this.fire('timeload', {
            time: time
        });
     }
  

});

L.timeDimension.layer.sodaHeatMap = function(options) {
    return new L.TimeDimension.Layer.SODAHeatMap(options);
};
