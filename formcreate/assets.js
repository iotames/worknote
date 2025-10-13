let api=$inject.api;
id=api.getValue("Fsj4mbu9ahsmdxc");
fetch('http://172.16.160.33:5678/webhook/getLedgerList/id?id='+id)
  .then(response => {
    if (!response.ok) { // 检查 HTTP 状态是否成功（2xx）
      throw new Error(`HTTP 错误！状态码：${response.status}`);
    }
    return response.json(); // 解析 JSON（也可以是 text()/blob() 等）
  })
  .then(data => {
 
  api.setValue("Fg4cmbu9ajc5e0c",data[0].asset_name);
  api.setValue("Fygnmbu9akjme3c",data[0].spec_model);
  api.setValue("Fddkmbum6womcec",data[0].unit);
  api.setValue("Fi68mbu9andae9c",data[0].original_price);
  api.setValue("Fv0kmbu9b3zremc",data[0].lost_price);
  api.setValue("F3uzmbu9b5ajepc",data[0].current_price);
  api.setValue("Fzldmbu9b6s1esc",data[0].title);
  
    console.log("inject.rule:", $inject.rule);
    console.log("inject.self", $inject.self);
  console.log("inject.option:", $inject.option);
  console.log("inject.args:", $inject.args);


    console.log('响应数据：', data);
  })
  .catch(error => {
    console.error('请求失败：', error);
  });