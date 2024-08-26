const express = require('express');
const router = express.Router();
const Container = require('../models/Container');

// Crear contenedor
router.post('/create', async (req, res) => {
    const { name, description } = req.body;

    try {
        const newContainer = new Container({ name, description, user: req.user._id });
        await newContainer.save();
        res.status(201).json({ message: 'Contenedor creado exitosamente' });
    } catch (error) {
        res.status(500).json({ message: 'Error al crear el contenedor' });
    }
});

// Buscar contenedores
router.get('/search', async (req, res) => {
    try {
        const containers = await Container.find({ user: req.user._id });
        res.status(200).json(containers);
    } catch (error) {
        res.status(500).json({ message: 'Error al buscar los contenedores' });
    }
});

// Modificar contenedor
router.put('/update/:id', async (req, res) => {
    const { id } = req.params;
    const { name, description } = req.body;

    try {
        const container = await Container.findOneAndUpdate(
            { _id: id, user: req.user._id },
            { name, description },
            { new: true }
        );
        if (!container) return res.status(404).json({ message: 'Contenedor no encontrado' });
        res.status(200).json({ message: 'Contenedor actualizado exitosamente', container });
    } catch (error) {
        res.status(500).json({ message: 'Error al actualizar el contenedor' });
    }
});

// Eliminar contenedor
router.delete('/delete/:id', async (req, res) => {
    const { id } = req.params;

    try {
        const container = await Container.findOneAndDelete({ _id: id, user: req.user._id });
        if (!container) return res.status(404).json({ message: 'Contenedor no encontrado' });
        res.status(200).json({ message: 'Contenedor eliminado exitosamente' });
    } catch (error) {
        res.status(500).json({ message: 'Error al eliminar el contenedor' });
    }
});

module.exports = router;