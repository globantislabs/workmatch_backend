/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("t86hiw9ot52mlci")

  // remove
  collection.schema.removeField("nzbwwdqf")

  // remove
  collection.schema.removeField("31t9jeb7")

  // remove
  collection.schema.removeField("lmv3y8hs")

  // remove
  collection.schema.removeField("iapwmz93")

  // remove
  collection.schema.removeField("zzjqbjy5")

  // remove
  collection.schema.removeField("e3gnalrn")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "4f0zlj5z",
    "name": "full_name",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "l1bs1j01",
    "name": "company_name",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "dsagxcw0",
    "name": "email",
    "type": "email",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "exceptDomains": null,
      "onlyDomains": null
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "kinwtvtd",
    "name": "phone",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "5lcgo1wi",
    "name": "inquiry",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "c7rcft6z",
    "name": "consent",
    "type": "bool",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {}
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("t86hiw9ot52mlci")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "nzbwwdqf",
    "name": "full_name",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "31t9jeb7",
    "name": "company_name",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "lmv3y8hs",
    "name": "email",
    "type": "email",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "exceptDomains": null,
      "onlyDomains": null
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "iapwmz93",
    "name": "phone",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "zzjqbjy5",
    "name": "inquiry",
    "type": "text",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "e3gnalrn",
    "name": "consent",
    "type": "bool",
    "required": true,
    "presentable": false,
    "unique": false,
    "options": {}
  }))

  // remove
  collection.schema.removeField("4f0zlj5z")

  // remove
  collection.schema.removeField("l1bs1j01")

  // remove
  collection.schema.removeField("dsagxcw0")

  // remove
  collection.schema.removeField("kinwtvtd")

  // remove
  collection.schema.removeField("5lcgo1wi")

  // remove
  collection.schema.removeField("c7rcft6z")

  return dao.saveCollection(collection)
})
