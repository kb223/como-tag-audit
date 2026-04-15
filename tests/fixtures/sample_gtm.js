// Minimal gtm.js fixture — just enough for the parser.
var google_tag_manager = {};
(function(){/* ...lots of minified bootstrap... */})();
var data = ({"resource":{"version":"123","macros":[],"tags":[
  {"function":"__ga4","tag_id":1,"instance_name":"GA4 Config"},
  {"function":"__awct","tag_id":2,"instance_name":"Google Ads Conv","consent_settings":{"consent":2,"cm":[{"type":0,"string":"ad_storage"},{"type":0,"string":"ad_user_data"}]}},
  {"function":"__html","tag_id":3,"instance_name":"Meta Pixel fbq init"},
  {"function":"__html","tag_id":4,"instance_name":"TikTok Pixel","consent_settings":{"consent":2,"cm":[{"type":0,"string":"ad_storage"}]}},
  {"function":"__img","tag_id":5,"instance_name":"Pinterest pintrk Conversion","consent_settings":{"consent":1,"cm":[{"type":0,"string":"ad_storage"}]}},
  {"function":"__html","tag_id":6,"instance_name":"Hotjar Tracking Snippet"},
  {"function":"__cl","tag_id":7,"instance_name":"All Clicks Listener"},
  {"function":"__fsl","tag_id":8,"instance_name":"Form Submit Listener"},
  {"function":"__cvt_12345","tag_id":9,"instance_name":"Conversion Linker v2"},
  {"function":"__gaawe","tag_id":10,"instance_name":"Enhanced Conversions"}
]}});
gtag('consent', 'default', {'ad_storage':'denied'});
