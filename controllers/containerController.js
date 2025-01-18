const Container = require('../models/Container');

exports.createContainer = async (req, res) => {
    try {
        const container = new Container(req.body);
        await container.save();
        res.status(201).send(container);
    } catch (error) {
        res.status(400).send({ error: 'Error al crear el contenedor' });
    }
};

exports.getContainers = async (req, res) => {
    try {
        const containers = await Container.find();
        res.status(200).send(containers);
    } catch (error) {
        res.status(400).send({ error: 'Error al obtener los contenedores' });
    }
};

exports.getContainerById = async (req, res) => {
    try {
        const container = await Container.findById(req.params.id);
        if (!container) {
            return res.status(404).send({ error: 'Contenedor no encontrado' });
        }
        res.status(200).send(container);
    } catch (error) {
        res.status(400).send({ error: 'Error al obtener el contenedor' });
    }
};

exports.updateContainer = async (req, res) => {
    try {
        const container = await Container.findByIdAndUpdate(
            req.params.id,
            req.body,
            { new: true },
        );
        if (!container) {
            return res.status(404).send({ error: 'Contenedor no encontrado' });
        }
        res.status(200).send(container);
    } catch (error) {
        res.status(400).send({ error: 'Error al actualizar el contenedor' });
    }
};

exports.deleteContainer = async (req, res) => {
    try {
        const container = await Container.findByIdAndDelete(req.params.id);
        if (!container) {
            return res.status(404).send({ error: 'Contenedor no encontrado' });
        }
        res.status(200).send({ message: 'Contenedor eliminado con éxito' });
    } catch (error) {
        res.status(400).send({ error: 'Error al eliminar el contenedor' });
    }
};
